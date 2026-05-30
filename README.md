# EV Charging Scheduler

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Change a weight
- Use the sliders in the UI, or edit the `weights` section of a scenario JSON in `data/scenarios/`.

## Add a new rule
- Update the CP-SAT constraints in `scheduler/solver.py` (e.g., add a new variable and constraint).
- If the rule should be tunable, add a new weight to the scenario JSON and the UI sliders.
