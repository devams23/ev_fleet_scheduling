# Copilot Instructions

## Build / Test / Lint
- No build, test, or lint commands are defined in this repo yet.

## Architecture (per docs/assesment_document.md)
- Target is a single Python + Streamlit app (one repo, one process).
- Scheduler reads scenario data files (5 scenarios) that define buses, operators, direction, departure times, and weights; route/stations should be data-driven.
- Scheduler outputs per-bus timelines (charges, waits, arrival) and per-station charging order; UI surfaces scenario selection, input data, and both outputs.

## Domain / Model conventions
- Route segments: Bengaluru → A (100 km) → B (120 km) → C (100 km) → D (120 km) → Kochi (100 km).
- Battery range is 240 km; charging always to full and takes 25 minutes; only A–D are charging stations.
- One charger per station; no backtracking; buses must never exceed range between charges.
- Weights (individual, operator, overall) must be tunable per scenario; Scenario 4 sets operator weight to 2.0.
- Scenario files are the authoritative data structure and must encode all 5 scenarios.

## Required docs (per spec)
- README.md: local run instructions, how to change a weight, how to add a new rule.
- ARCHITECTURE.md: scheduler approach, data model, anticipated future changes, examples for changing weights/adding rules, and assumptions.
