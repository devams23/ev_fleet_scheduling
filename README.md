# EV Charging Scheduler

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Scenario files are the single source of truth
All scheduler inputs live in `data/scenarios/scenario_*.json` and are read by both the UI and solver:
- `weights`: objective tuning (`individual`, `operator`, `overall`)
- `parameters`: runtime rules (`speed_kmph`, `battery_range_km`, `charge_minutes`, `chargers_per_station`)
- `route`, `stations`, and `buses` (with `origin`/`destination`)

If you need to change behavior, change scenario JSON first.

## Change weights or scenario parameters
Edit a scenario file directly, for example:
```json
{
  "weights": { "individual": 1.0, "operator": 2.0, "overall": 1.0 },
  "parameters": {
    "speed_kmph": 60,
    "battery_range_km": 240,
    "charge_minutes": 25,
    "chargers_per_station": 1
  }
}
```

You can also use UI sliders for temporary weight experiments, but committed behavior should be captured in scenario files.

## Add a new rule
- Add/adjust the rule in `scheduler/solver.py`.
- If it should be tunable per scenario, add the field under `parameters` or `weights` in scenario JSON and wire it through the model/UI.
