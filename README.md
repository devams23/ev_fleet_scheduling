# EV Charging Scheduler

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Change a weight
- Use the sliders in the UI, or edit the `weights` section of a scenario JSON in `data/scenarios/`:
```json
{
  "weights": { "individual": 1.0, "operator": 2.0, "overall": 1.0 }
}
```

## Add a new rule
- Update the CP-SAT constraints in `scheduler/solver.py` (e.g., add a new variable and constraint). Example: cap wait time to 30 minutes per station.
```python
max_wait = 30
model.Add(wait <= max_wait).OnlyEnforceIf(stop)
```
- If the rule should be tunable, add a new weight to the scenario JSON and the UI sliders.
