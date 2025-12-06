import random

from flask import Flask, jsonify, request
from ortools.linear_solver import pywraplp

app = Flask(__name__)

WEAPONS = ["foil", "epee", "sabre"]


def run_solver(fencers, direction=1, all_male=False):
    # Set up the solver
    solver = pywraplp.Solver.CreateSolver("CBC")
    n = len(fencers)
    teams = n // 3

    # VARIABLES: Binary x[i,t,w] = 1 if fencer i is assigned to team t in weapon w, otherwise 0.
    x = {}
    for i in range(n):
        for t in range(teams):
            for w in WEAPONS:
                x[(i, t, w)] = solver.BoolVar(f"x_{i}_{t}_{w}")

    # CONSTRAINTS: Each fencer assigned exactly once
    for i in range(n):
        solver.Add(sum(x[(i, t, w)] for t in range(teams) for w in WEAPONS) == 1)

    # CONSTRAINTS: Each team has exactly one of each weapon
    for t in range(teams):
        for w in WEAPONS:
            solver.Add(sum(x[(i, t, w)] for i in range(n)) == 1)

    # CONSTRAINTS: Each team must have 1+ F fencers
    if not all_male:
        for t in range(teams):
            solver.Add(
                sum(
                    x[(i, t, w)]
                    for i in range(n)
                    for w in WEAPONS
                    if fencers[i]["category"].upper() == "F"
                )
                >= 1
            )

    # CONSTRAINTS: Each team must have 1+ M fencers
    for t in range(teams):
        solver.Add(
            sum(
                x[(i, t, w)]
                for i in range(n)
                for w in WEAPONS
                if fencers[i]["category"].upper() == "M"
            )
            >= 1
        )

    # OBJECTIVE: Maximise/Minimize preference score
    objective = solver.Objective()
    for i in range(n):
        for t in range(teams):
            for w in WEAPONS:
                if direction == 1:
                    score = fencers[i]["preference"][w]
                else:
                    score = 6 - fencers[i]["preference"][w]
                objective.SetCoefficient(x[(i, t, w)], score)
    objective.SetMaximization()

    # SOLUTION - PART1: Linear optimization
    status = solver.Solve()
    output = []
    for t in range(teams):
        team_members = {}
        for w in WEAPONS:
            for i in range(n):
                if x[(i, t, w)].solution_value() > 0.5:
                    team_members[w] = {
                        "name": fencers[i]["name"],
                        "category": fencers[i]["category"],
                        "preference": fencers[i]["preference"][w],
                    }
        output.append({"team": t + 1, "members": team_members})
    return output


@app.route("/solve", methods=["POST"])
def solve():
    # Get data and calculate M/F particpant numbers
    fencers = request.get_json()["fencers"]
    reserves = []
    n_f = len([fencer for fencer in fencers if fencer["category"].upper() == "F"])
    n_m = len([fencer for fencer in fencers if fencer["category"].upper() == "M"])
    print("Participants:", len(fencers))
    print("M:", n_m, " ; F:", n_f)

    # If the number of F is not enough to have 1 per team, randomly exclude M fencers until it is
    if 3 * n_f < len(fencers):
        to_remove = len(fencers) - 3 * n_f
        m_fencers = [fencer for fencer in fencers if fencer["category"].upper() == "M"]
        reserves = reserves + random.sample(m_fencers, to_remove)
        fencers = [fencer for fencer in fencers if fencer not in reserves]

    # I don't think we'll have this, but if we have so many F that we get F only teams remove some F
    # if n_f > teams*2:
    #     to_remove = n_f - teams*2
    #     f_fencers = [fencer for fencer in fencers if fencer["category"].upper() == "F"]
    #     reserves = reserves + random.sample(f_fencers, to_remove)
    #     fencers = [fencer for fencer in fencers if fencer not in reserves]
    #     n_f = len([fencer for fencer in fencers if fencer["category"].upper() == "F"])
    #     n = len(fencers)
    #     teams = len(fencers) // 3

    # If the number of fencers is not a multiple of 3, randomly exclude fencers until it is
    if len(fencers) % 3 != 0:
        to_remove = len(fencers) % 3
        m_fencers = [fencer for fencer in fencers if fencer["category"].upper() == "M"]
        reserves = reserves + random.sample(m_fencers, to_remove)
        fencers = [fencer for fencer in fencers if fencer not in reserves]

    # Set up the solver
    output = run_solver(fencers)

    # We might still have some fencers in the reserves to assign
    # If it's more than 3 then we form teams
    if len(reserves) >= 3:
        teams = len(reserves) // 3
        fencers = random.sample(reserves, teams * 3)
        reserves = [fencer for fencer in reserves if fencer not in fencers]
        output_reserves = run_solver(fencers, direction=-1, all_male=True)
        for team in output_reserves:
            team["team"] = team["team"] + len(output)
        output = output + output_reserves

    # For the last reserves we assign them to their favorite weapon and then to a random team where the F fencer has not that weapon.
    if len(reserves) > 0:
        for reserve in reserves:
            # Determine sorted weapons by preference (descending)
            # stored as list of (weapon, score)
            sorted_prefs = sorted(
                reserve["preference"].items(), key=lambda item: item[1], reverse=True
            )
            favorite_weapon = sorted_prefs[0][0]
            
            # Candidates for 2F teams: Any weapon with score >= 3 is acceptable if it matches.
            # But we prefer Favorite over 2nd Favorite. 
            # Actually, standard matching logic:
            # We want to find a valid assignment.
            
            print(f"DEBUG: Processing Reserve {reserve['name']}, Fav: {favorite_weapon}")
            priority_options = [] # List of (team, weapon_to_use)
            other_options = []    # List of (team, weapon_to_use)

            for team in output:
                # Constraint: Max 1 reserve per team.
                if "reserves" in team and len(team["reserves"]) > 0:
                    continue

                members = team["members"]
                f_weapons_assigned = [
                    w for w, m in members.items() if m["category"].upper() == "F"
                ]
                num_f = len(f_weapons_assigned)
                # print(f"DEBUG: Team {team['team']} has {num_f} Fencers. Assigned F-Weapons: {f_weapons_assigned}")

                if num_f == 0:
                     # 3M constraint: Exclude
                     continue

                if num_f >= 2:
                    # 2F+ Team Priority Rule
                    # 1. Try Favorite Weapon
                    if favorite_weapon in f_weapons_assigned:
                        priority_options.append((team, favorite_weapon))
                    else:
                        # 2. Try Secondary Weapons (Score >= 3)
                        # Find the first one that matches
                        found_secondary = False
                        for w, score in sorted_prefs:
                            if w == favorite_weapon: continue
                            if score < 3: break # sorted desc, so we can stop
                            
                            if w in f_weapons_assigned:
                                priority_options.append((team, w))
                                found_secondary = True
                                break # Use the best available secondary
                        
                elif num_f == 1:
                    # 1F Team Rule
                    f_weapon = f_weapons_assigned[0]
                    # print(f"DEBUG: 1F Check. Fav: {favorite_weapon}, F_Web: {f_weapon}")
                    
                    # Check Favorite first
                    if favorite_weapon != f_weapon:
                         other_options.append((team, favorite_weapon))
                    else:
                        # Favorite matches F-weapon.
                        # If Reserve is M, we MUST NOT match. So we look for a secondary weapon.
                         if reserve["category"].upper() == "M":
                            # print(f"DEBUG: Reserve is M. Scanning Secondary. Sorted: {sorted_prefs}")
                            for w, score in sorted_prefs:
                                if w != f_weapon:
                                    # Found a non-conflicting weapon
                                    # print(f"DEBUG: Found alternative: {w}")
                                    other_options.append((team, w))
                                    break
                         else:
                            # Also check for F? Or just ignore? current behavior allows skip.
                            # Standardizing on trying to find a spot.
                            for w, score in sorted_prefs:
                                if w != f_weapon:
                                    other_options.append((team, w))
                                    break
            
            # print(f"DEBUG: Priority: {priority_options}")
            # print(f"DEBUG: Other: {other_options}")

            # Selection Logic
            final_selection = None # (team, weapon)

            if priority_options:
                final_selection = random.choice(priority_options)
            elif other_options:
                final_selection = random.choice(other_options)
            else:
                # Fallback: Assign to ANY team > 0F without reserve
                # Use Favorite Weapon as default for fallback
                teams_without_reserves = [
                    t for t in output 
                    if ("reserves" not in t or len(t["reserves"]) == 0)
                    and len([m for m in t["members"].values() if m["category"].upper() == "F"]) > 0
                ]
                
                if teams_without_reserves:
                     t = random.choice(teams_without_reserves)
                     final_selection = (t, favorite_weapon)
                else:
                     # Absolute fallback (try to find any >0F team even if reserve exists? Or just 3M?)
                     # Try to avoid 3M if possible.
                     teams_with_f = [
                        t for t in output 
                        if len([m for m in t["members"].values() if m["category"].upper() == "F"]) > 0
                     ]
                     if teams_with_f:
                         t = random.choice(teams_with_f)
                         final_selection = (t, favorite_weapon)
                     else:
                         t = random.choice(output)
                         final_selection = (t, favorite_weapon)

            # Apply Assignment
            target_team, assigned_weapon = final_selection
            
            reserve["weapon"] = assigned_weapon
            
            if "reserves" not in target_team:
                target_team["reserves"] = []
            target_team["reserves"].append(reserve)

    # Return results
    return jsonify({"status": "ok", "teams": output})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
