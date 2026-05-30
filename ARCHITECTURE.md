# Architecture

## Scheduler approach
The scheduler builds a CP-SAT model with optional charging intervals for each bus at each station. It enforces non-overlap at each station, range feasibility between charging points, and minimizes a weighted objective (individual wait, operator fairness, overall makespan). A time limit returns the best feasible schedule if optimality is not proven.

## Data model
Scenario JSON files encode the route segments, station list, weights, and bus schedule rows. These files are the authoritative input and drive both the solver and UI.

## Future changes
- **New constraint:** add a new decision variable and constraint in `scheduler/solver.py`.
- **New weight:** extend the JSON `weights` object, add a UI slider, and include the term in the objective.

## Assumptions
- 60 km/h travel speed.
- 25-minute full charge.
- One charger per station, no backtracking.
