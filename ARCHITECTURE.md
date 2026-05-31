# Architecture

## Scheduler approach
The scheduler builds a CP-SAT model with optional charging intervals for each bus at each station. It enforces non-overlap at each station, range feasibility between charging points, and minimizes a weighted objective (individual wait, operator fairness, overall makespan). A time limit returns the best feasible schedule if optimality is not proven.

**Why CP-SAT fits this problem:** the schedule has hard constraints (battery range, one charger per station) and soft tradeoffs (wait time vs fairness vs makespan). CP-SAT handles discrete decisions (which stations to stop at) and time window constraints cleanly, and can prove optimality for a small-to-midsize fleet while still returning a best-found solution under a time limit.

## Data model
Scenario JSON files encode the route segments, station list, weights, and bus schedule rows. These files are the authoritative input and drive both the solver and UI.

```json
{
  "scenario_id": "scenario_1",
  "weights": { "individual": 1.0, "operator": 1.0, "overall": 1.0 },
  "parameters": {
    "speed_kmph": 60,
    "battery_range_km": 240,
    "charge_minutes": 25,
    "chargers_per_station": 1
  },
  "route": [
    { "from": "Bengaluru", "to": "A", "distance_km": 100 },
    { "from": "A", "to": "B", "distance_km": 120 },
    { "from": "B", "to": "C", "distance_km": 100 },
    { "from": "C", "to": "D", "distance_km": 120 },
    { "from": "D", "to": "Kochi", "distance_km": 100 }
  ],
  "stations": ["A", "B", "C", "D"],
  "buses": [
    {
      "bus_id": "bus-BK-01",
      "operator": "kpn",
      "origin": "Bengaluru",
      "destination": "Kochi",
      "depart_time": "19:00"
    }
  ]
}
```

`parameters` and `weights` control solver behavior, `route` defines distances, `stations` defines charging stops, and `buses` define the demand signal with explicit `origin`/`destination`. The solver and UI both read directly from this structure.

## Future changes
- **Different route distances or more segments:** update the `route` list in a scenario JSON; travel times recompute from data.
- **More/less charging stations:** update the `stations` list; the solver reads the stations from data.
- **New operators or more buses:** add rows in `buses`; the solver groups by `operator` dynamically.
- **Different departure schedules or directions:** change `depart_time`, `origin`, and `destination` in `buses`.
- **Different weight tuning:** edit `weights` in scenario JSON (UI sliders are for interactive experimentation).
- **Different core operating assumptions:** edit `parameters` in scenario JSON.
- **New scenario variations:** add another JSON file in `data/scenarios/` with the same schema.

## Assumptions
- Scenario files are the single source of truth for weights and operational parameters.
- `parameters.speed_kmph` drives travel-time conversion from route distance.
- `parameters.battery_range_km` is the max distance between required charges.
- `parameters.charge_minutes` is the fixed full-charge duration.
- `parameters.chargers_per_station` controls station charging capacity.
- Bus `origin` and `destination` must match route endpoints; no backtracking.

## Code examples

### Change a weight
```json
{
  "weights": { "individual": 1.0, "operator": 2.0, "overall": 1.0 }
}
```

### Change a scenario parameter
```json
{
  "parameters": {
    "speed_kmph": 60,
    "battery_range_km": 240,
    "charge_minutes": 25,
    "chargers_per_station": 1
  }
}
```

### Add a new rule (example: cap wait time to 30 minutes)
```python
# scheduler/solver.py (inside the station loop)
max_wait = 30
model.Add(wait <= max_wait).OnlyEnforceIf(stop)
```
