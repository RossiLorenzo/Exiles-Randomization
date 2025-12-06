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
            # Determine favorite weapon (highest preference score)
            favorite_weapon = max(reserve["preference"], key=reserve["preference"].get)
            reserve["weapon"] = favorite_weapon

            priority_teams = []
            other_valid_teams = []

            for team in output:
                # Constraint: Max 1 reserve per team.
                if "reserves" in team and len(team["reserves"]) > 0:
                    continue

                members = team["members"]
                f_weapons_assigned = [
                    w for w, m in members.items() if m["category"].upper() == "F"
                ]
                num_f = len(f_weapons_assigned)

                if num_f >= 2:
                    # If team has 2 or 3 F: reserve must have favorite weapon SAME as one of the F fencers
                    if favorite_weapon in f_weapons_assigned:
                        priority_teams.append(team)
                elif num_f == 1:
                    # If team has 1 F: reserve must NOT have same weapon as the F fencer
                    if favorite_weapon != f_weapons_assigned[0]:
                        other_valid_teams.append(team)

            # Assign to a random valid team, prioritizing those with 2+ Fencers
            if priority_teams:
                target_team = random.choice(priority_teams)
            elif other_valid_teams:
                target_team = random.choice(other_valid_teams)
            else:
                # Fallback: Assign to ANY team that doesn't have a reserve yet
                teams_without_reserves = [t for t in output if "reserves" not in t or len(t["reserves"]) == 0]
                if teams_without_reserves:
                     target_team = random.choice(teams_without_reserves)
                else:
                     # Absolute fallback
                     target_team = random.choice(output)

            if "reserves" not in target_team:
                target_team["reserves"] = []
            target_team["reserves"].append(reserve)

    # Return results
    return jsonify({"status": "ok", "teams": output})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
