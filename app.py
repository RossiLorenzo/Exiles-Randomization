import random

from flask import Flask, jsonify, request
from ortools.linear_solver import pywraplp

app = Flask(__name__)

WEAPONS = ["foil", "epee", "sabre"]


@app.route("/solve", methods=["POST"])
def solve():
    # Get data and calculate M/F particpant numbers
    fencers = request.get_json()["fencers"]
    reserves = []
    n_f = len([fencer for fencer in fencers if fencer["category"].upper() == "F"])
    n_m = len([fencer for fencer in fencers if fencer["category"].upper() == "M"])
    print("Participants:", n)
    print("M:", n_m, " ; F:", n_f)

    # If the number of F is not enought to have 1 per team, randomly exclude M fencers until it is
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
    solver = pywraplp.Solver.CreateSolver("CBC")
    n = len(fencers)
    teams = n // 3
    print("Participants:", n, "Teams", teams)

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

    # CONSTRAINTS: Each team must has 1+ F fencers
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

    # CONSTRAINTS: Each team must have a max of 2 F fencers
    for t in range(teams):
        solver.Add(
            sum(
                x[(i, t, w)]
                for i in range(n)
                for w in WEAPONS
                if fencers[i]["category"].upper() == "F"
            )
            <= 2
        )

    # OBJECTIVE: Maximise preference score
    objective = solver.Objective()
    for i in range(n):
        for t in range(teams):
            for w in WEAPONS:
                score = fencers[i]["preference"][w]
                objective.SetCoefficient(x[(i, t, w)], score)
    objective.SetMaximization()

    # SOLUTION - PART1: Linear optimization
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

    # We might still have some fencers in the reserves to assign
    # If it's more than 3 then we form teams
    # If it's less than 3 we assign them to existing teams
    # if len(reserves) >= 3:

    # Return results
    return jsonify({"status": "ok", "teams": output})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
