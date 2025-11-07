from flask import Flask, jsonify, request
from ortools.linear_solver import pywraplp

app = Flask(__name__)

input = [
    {
        "name": "Fencer1",
        "gender": "M",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer2",
        "gender": "F",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer3",
        "gender": "F",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer4",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer5",
        "gender": "M",
        "preference": {"foil": 1, "epee": 3, "sabre": 2},
    },
    {
        "name": "Fencer6",
        "gender": "F",
        "preference": {"foil": 1, "epee": 3, "sabre": 2},
    },
    {
        "name": "Fencer7",
        "gender": "M",
        "preference": {"foil": 3, "epee": 1, "sabre": 2},
    },
    {
        "name": "Fencer8",
        "gender": "F",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer9",
        "gender": "F",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer10",
        "gender": "M",
        "preference": {"foil": 3, "epee": 1, "sabre": 2},
    },
    {
        "name": "Fencer11",
        "gender": "M",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer12",
        "gender": "F",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer13",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer14",
        "gender": "F",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer15",
        "gender": "M",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer16",
        "gender": "M",
        "preference": {"foil": 3, "epee": 1, "sabre": 2},
    },
    {
        "name": "Fencer17",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer18",
        "gender": "M",
        "preference": {"foil": 3, "epee": 1, "sabre": 2},
    },
    {
        "name": "Fencer19",
        "gender": "M",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer20",
        "gender": "F",
        "preference": {"foil": 1, "epee": 2, "sabre": 3},
    },
    {
        "name": "Fencer21",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer22",
        "gender": "F",
        "preference": {"foil": 1, "epee": 3, "sabre": 2},
    },
    {
        "name": "Fencer23",
        "gender": "M",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer24",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer25",
        "gender": "F",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer26",
        "gender": "F",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer27",
        "gender": "M",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer28",
        "gender": "F",
        "preference": {"foil": 1, "epee": 3, "sabre": 2},
    },
    {
        "name": "Fencer29",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer30",
        "gender": "F",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer31",
        "gender": "M",
        "preference": {"foil": 3, "epee": 1, "sabre": 2},
    },
    {
        "name": "Fencer32",
        "gender": "F",
        "preference": {"foil": 1, "epee": 3, "sabre": 2},
    },
    {
        "name": "Fencer33",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer34",
        "gender": "F",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer35",
        "gender": "M",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer36",
        "gender": "M",
        "preference": {"foil": 1, "epee": 2, "sabre": 3},
    },
    {
        "name": "Fencer37",
        "gender": "M",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer38",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
    {
        "name": "Fencer39",
        "gender": "M",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer40",
        "gender": "M",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer41",
        "gender": "F",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer42",
        "gender": "M",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer43",
        "gender": "M",
        "preference": {"foil": 3, "epee": 1, "sabre": 2},
    },
    {
        "name": "Fencer44",
        "gender": "F",
        "preference": {"foil": 3, "epee": 2, "sabre": 1},
    },
    {
        "name": "Fencer45",
        "gender": "M",
        "preference": {"foil": 2, "epee": 3, "sabre": 1},
    },
    {
        "name": "Fencer46",
        "gender": "M",
        "preference": {"foil": 2, "epee": 1, "sabre": 3},
    },
]

WEAPONS = ["foil", "epee", "sabre"]


@app.post("/solve")
def solve():
    return request
    fencers = request.get_json()["fencers"]
    # If the number of fencers is not a multiple of 3, randomly exclude male fencers until it is
    if len(fencers) % 3 != 0:
        to_remove = len(fencers) % 3
        male_fencers = [fencer for fencer in fencers if fencer["gender"].upper() == "M"]
        reserves = random.sample(male_fencers, to_remove)
    fencers = [fencer for fencer in fencers if fencer not in reserves]

    # If the number of female fencers is not enought to have 1 per team, randomly exclude male fencers until it is
    n_females = len([fencer for fencer in fencers if fencer["gender"].upper() == "F"])
    if 3 * n_females < len(fencers):
        to_remove = len(fencers) - 3 * n_females
        male_fencers = [fencer for fencer in fencers if fencer["gender"].upper() == "M"]
        reserves = reserves + random.sample(male_fencers, to_remove)
    fencers = [fencer for fencer in fencers if fencer not in reserves]

    # Set up the solver
    solver = pywraplp.Solver.CreateSolver("CBC")
    n = len(fencers)
    teams = len(fencers) // 3

    # VARIABLES: Binary x[i,t,w] = 1 if fencer i is assigned to team t in weapon w, otherwise 0.
    x = {}
    for i in range(n):
        for t in range(teams):
            for w in WEAPONS:
                x[(i, t, w)] = solver.BoolVar(f"x_{i}_{t}_{w}")

    # CONSTRAINTS: Each fencer assigned exactly once
    for i in range(n):
        solver.Add(sum(x[(i, t, w)] for t in range(teams) for w in WEAPONS) == 1)

    # CONSTRAINTS: Each has exactly one of each weapon
    for t in range(teams):
        for w in WEAPONS:
            solver.Add(sum(x[(i, t, w)] for i in range(n)) == 1)

    # CONSTRAINTS: Each team must have at least one female fencer
    for t in range(teams):
        solver.Add(
            sum(
                x[(i, t, w)]
                for i in range(n)
                for w in WEAPONS
                if fencers[i]["gender"].upper() == "F"
            )
            >= 1
        )

    # OBJECTIVE: maximise preference score
    objective = solver.Objective()
    for i in range(n):
        for t in range(teams):
            for w in WEAPONS:
                pref_rank = fencers[i]["preference"][w]
                score = 4 - pref_rank
                objective.SetCoefficient(x[(i, t, w)], score)
    objective.SetMaximization()

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        return jsonify({"status": "fail", "teams": {}})
    # Extract solution
    output = []
    for t in range(teams):
        team_members = {}
        for w in WEAPONS:
            for i in range(n):
                if x[(i, t, w)].solution_value() > 0.5:
                    team_members[w] = {
                        "name": fencers[i]["name"],
                        "gender": fencers[i]["gender"],
                        "preference": fencers[i]["preference"][w],
                    }
        output.append({"team": t + 1, "members": team_members})
    return jsonify({"status": "ok", "teams": output})
