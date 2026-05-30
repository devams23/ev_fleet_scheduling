# EV Charging Scheduler Design (CP-SAT)

## Context and goals
- Build a single Python + Streamlit app that schedules EV buses across stations A–D.
- Scenarios are data-driven JSON files (5 scenarios) with route, stations, weights, and schedules.
- Output per-bus timelines (travel, wait, charge) and per-station charging order.
- Use exact optimization (CP-SAT) with a reasonable time limit and best-found solution if optimality is not proven.
- Weights (individual, operator, overall) are editable in the UI; scenario 4 sets operator weight to 2.0 by default.

## Non-goals
- Real-time traffic, dynamic pricing, or battery degradation modeling.
- Multi-process or multi-service architecture.

## Assumptions
- Travel speed: 60 km/h.
- Charging: always to full, fixed 25 minutes.
- Stations: A–D only, one charger per station.
- Buses may wait in a queue; no backtracking.
- Range constraint: must never exceed 240 km between charges (including endpoints).

## Architecture
1. **Scenario loader/validator**: reads JSON, validates schema, normalizes times.
2. **Time model**: converts segment distances into travel minutes.
3. **CP-SAT builder**: constructs variables, constraints, and objective.
4. **Solver runner**: executes CP-SAT with time limit, returns best solution.
5. **Solution formatter**: builds per-bus timelines and per-station order.
6. **Streamlit UI**: scenario picker, weight sliders, run button, tables.

## Scenario data model (JSON)
```json
{
  "scenario_id": "scenario_1",
  "weights": { "individual": 1.0, "operator": 1.0, "overall": 1.0 },
  "route": [
    { "from": "Bengaluru", "to": "A", "distance_km": 100 },
    { "from": "A", "to": "B", "distance_km": 120 },
    { "from": "B", "to": "C", "distance_km": 100 },
    { "from": "C", "to": "D", "distance_km": 120 },
    { "from": "D", "to": "Kochi", "distance_km": 100 }
  ],
  "stations": ["A", "B", "C", "D"],
  "buses": [
    { "bus_id": "B1", "operator": "KPN", "direction": "Bengaluru->Kochi", "depart_time": "09:00" }
  ]
}
```

## CP-SAT model
**Indices**
- For each bus, derive ordered station sequence based on direction.

**Decision variables**
- `stop[b,s]` ∈ {0,1} for each bus and station along its direction.
- `arrival[b,s]`, `start_charge[b,s]`, `end_charge[b,s]` (minutes).
- `wait[b,s]` (minutes) where `wait = start_charge - arrival`.

**Constraints**
- **Range**: distance between consecutive charges (or endpoint) ≤ 240 km.
- **Timing**: `arrival` = departure + travel + previous charge + previous wait (big‑M when `stop=0`).
- **Charge time**: `end_charge = start_charge + 25` when `stop=1`.
- **Non-overlap**: for each station, charging intervals do not overlap (single charger).
- **Queueing**: `wait ≥ 0` and only applies when `stop=1`.

**Objective**
Minimize weighted sum:
- **Individual**: total wait time across all buses.
- **Operator**: max total wait per operator minus min total wait per operator.
- **Overall**: makespan (latest arrival at destination).

Solver runs with a time limit; if not optimal, the best feasible solution is returned and labeled accordingly.

## UI and outputs
- **Inputs**: scenario picker, editable weight sliders, “Run schedule” button, input table.
- **Outputs**:
  - Per-bus timeline table: segment type (travel/wait/charge), start, end, station (if applicable).
  - Per-station charging order: ordered list of bus_id with start/end times and operator.

## Error handling
- Invalid scenario schema or impossible reachability → Streamlit error and no solve.
- Solver infeasible → show infeasible status and diagnostics (if available).
- Solver time limit → show best-found status and objective value.

## Testing
- Unit checks for time conversion and reachability constraints.
- Small synthetic scenario with known feasible schedule.

## Extensibility
- New rules become new constraints or objective terms in the CP-SAT builder.
- New scenarios are added as JSON files with the same schema.
