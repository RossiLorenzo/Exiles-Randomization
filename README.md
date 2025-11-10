# Exiles - Random Team/Weapon Assignment - Technical Details

## Context
For the first time ever, the Kent [Exiles](https://tomflecs.wixsite.com/thekentexiles) competition will trial a new format in which participants enter **individually** and not in already formed teams. Both weapon assignment and team assignment are random.

To minimize kit swaps and to allow the majority of the participants to fence their best weapon, when entering the competition each fencer was asked to rank their favorite weapon choices.

## Methodology
Maximizing the number of fencers participating in the competition with their favorite weapon, while still respecting the basic Exiles rules, it's a classic mathematical optimization problem and it can be solved with [Integer Linear Programming (ILP)](https://en.wikipedia.org/wiki/Integer_programming).

The constraints to respect are:
* Every team has 3 fencers. [^1]
* Every team has 1 fencer for each weapon (1 foil, 1 epee, 1 sabre).
* Every team has at least 1 female fencer. [^2]

The objective function is:
* Maximize the overall score of the self-selected favorite weapon choices.

[^1] If the number of participants is not exactly divisible by 3, we have to create at least 1 team with 4 fencers one of which is a reserve fencer.
[^2] If the number of female participants is not enought to have all teams with 1+ female fencer, we have deciced to create male only teams. However, to keep the competition as fair as possible in those teams we optimize so that all fencers are randomly assigned to their **least** favorite weapons instead.

## Implementation Details
For complete transparency we provide in this repo the full end-to-end implementation of this ILP problem.

### Step1: Raw Data
Data comes from this [Google Sheet](https://docs.google.com/spreadsheets/d/1h5XDZbBgbXeeHlfMRaI8xbgHBjp4n94oiH3WDPw23Aw/edit?usp=sharing) collecting the responses to the entry form. Each participant will have ranked their favorite weapons with a score from 1 to 5.

### Step2: Data Reshaping
The data is reshaped in the `buildPayload` function of the [`app_script`](https://github.com/RossiLorenzo/Exiles-Randomization/blob/main/app_script.gs) Google Script.

### Step3: API Call to Python code
The Python code contained in [`app.py`](https://github.com/RossiLorenzo/Exiles-Randomization/blob/main/app.py) is then triggered by the `callSolver` function of the [`app_script`](https://github.com/RossiLorenzo/Exiles-Randomization/blob/main/app_script.gs) Google Script. This code maximizes the solution `ortools`.
The deployement of the Python code is handled authomatically at each push by Heroku.
Note that in this repo I have removed the URL in the [`app_script`](https://github.com/RossiLorenzo/Exiles-Randomization/blob/main/app_script.gs) code to avoid malicious use. If you are intersted and want to try the API yourself please send me a message and I can share the endpoint with you.

### Step4: Write Optimal teams
The `writeAssignedTeams` function of the [`app_script`](https://github.com/RossiLorenzo/Exiles-Randomization/blob/main/app_script.gs) Google Script formats the results in tabular format and writes the raw results into the (hidden) `Assigned_Teams_Raw` tab of the [Google Sheet](https://docs.google.com/spreadsheets/d/1h5XDZbBgbXeeHlfMRaI8xbgHBjp4n94oiH3WDPw23Aw/edit?usp=sharing).

### Step5: Visualize final results
Finally, all the data is pulled back together and formatted nicely into
