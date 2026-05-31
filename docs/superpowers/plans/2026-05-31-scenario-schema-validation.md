# Scenario Schema + Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update scenario schema loading to the new parameters/origin/destination/time format and validate it with updated tests.

**Architecture:** Keep scenario loading in `scheduler\scenario.py` with strict schema validation, time parsing, and explicit dataclasses. Tests in `tests\test_scenario.py` define the new JSON schema and expected validations. No changes to scenario JSON data files.

**Tech Stack:** Python 3, unittest

---

## File Structure

- Modify: `tests\test_scenario.py` — replace with new schema tests.
- Modify: `scheduler\scenario.py` — add parameters/origin/destination/time validation and updated dataclasses.

---

### Task 1: Update scenario tests to the new schema

**Files:**
- Modify: `tests\test_scenario.py`

- [ ] **Step 1: Replace test file contents**

```python
import json
import tempfile
import unittest
from pathlib import Path

from scheduler.scenario import load_scenario


class ScenarioTests(unittest.TestCase):
    def _write_temp_scenario(self, data: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(data, tmp)
        tmp.close()
        return Path(tmp.name)

    def test_load_scenario_parses_times_and_weights(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["A"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        scenario = load_scenario(path)

        self.assertEqual(scenario.weights.individual, 1.0)
        self.assertEqual(scenario.parameters.battery_range_km, 240)
        self.assertEqual(scenario.buses[0].depart_minute, 570)
        self.assertEqual(scenario.buses[0].origin, "Bengaluru")

    def test_load_scenario_rejects_missing_station(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": [],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)

    def test_load_scenario_rejects_bad_time_format(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["A"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "9:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)

    def test_load_scenario_rejects_station_mismatch(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["B"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)

    def test_all_scenarios_load(self):
        for name in [
            "data/scenarios/scenario_1.json",
            "data/scenarios/scenario_2.json",
            "data/scenarios/scenario_3.json",
            "data/scenarios/scenario_4.json",
            "data/scenarios/scenario_5.json",
        ]:
            scenario = load_scenario(name)
            self.assertGreaterEqual(len(scenario.buses), 4)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run scenario tests (expect failure)**

Run: `python -m unittest tests\test_scenario.py -v`  
Expected: FAIL with missing `parameters`/`origin`/`destination` fields or time validation errors.

---

### Task 2: Update scenario schema + validation

**Files:**
- Modify: `scheduler\scenario.py`

- [ ] **Step 1: Replace schema definitions and validation**

```python
from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import List


@dataclass(frozen=True)
class Weights:
    individual: float
    operator: float
    overall: float


@dataclass(frozen=True)
class Parameters:
    speed_kmph: int
    battery_range_km: int
    charge_minutes: int
    chargers_per_station: int


@dataclass(frozen=True)
class RouteSegment:
    start: str
    end: str
    distance_km: int


@dataclass(frozen=True)
class Bus:
    bus_id: str
    operator: str
    origin: str
    destination: str
    depart_time: str
    depart_minute: int


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    weights: Weights
    parameters: Parameters
    route: List[RouteSegment]
    stations: List[str]
    buses: List[Bus]


_TIME_RE = re.compile(r"^\\d{2}:\\d{2}$")


def parse_time_to_minutes(value: str) -> int:
    if not _TIME_RE.match(value):
        raise ValueError(f"Invalid time format: {value}")
    hours, minutes = int(value[0:2]), int(value[3:5])
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        raise ValueError(f"Invalid time value: {value}")
    return hours * 60 + minutes


def _route_nodes(route: list[dict]) -> List[str]:
    if not route:
        raise ValueError("Scenario must define a route")
    nodes = [route[0]["from"]]
    for segment in route:
        if nodes[-1] != segment["from"]:
            raise ValueError("Route segments must be contiguous")
        nodes.append(segment["to"])
    return nodes


def _validate_scenario(data: dict) -> None:
    stations = data.get("stations", [])
    if not stations:
        raise ValueError("Scenario must define at least one station")
    for key in ("weights", "route", "buses", "parameters"):
        if key not in data:
            raise ValueError(f"Scenario missing '{key}'")

    params = data["parameters"]
    for key in ("speed_kmph", "battery_range_km", "charge_minutes", "chargers_per_station"):
        if key not in params:
            raise ValueError(f"Scenario parameters missing '{key}'")

    nodes = _route_nodes(data["route"])
    intermediate = nodes[1:-1]
    if stations != intermediate:
        raise ValueError("Stations must match intermediate route nodes")

    route_start, route_end = nodes[0], nodes[-1]
    for bus in data["buses"]:
        origin = bus.get("origin")
        destination = bus.get("destination")
        if origin is None or destination is None:
            raise ValueError("Bus must define origin and destination")
        if origin == destination:
            raise ValueError("Bus origin and destination must differ")
        if {origin, destination} != {route_start, route_end}:
            raise ValueError("Bus origin/destination must match route endpoints")
        parse_time_to_minutes(bus["depart_time"])


def load_scenario(path: Path) -> Scenario:
    data = json.loads(Path(path).read_text())
    _validate_scenario(data)

    weights = Weights(
        individual=float(data["weights"]["individual"]),
        operator=float(data["weights"]["operator"]),
        overall=float(data["weights"]["overall"]),
    )
    parameters = Parameters(
        speed_kmph=int(data["parameters"]["speed_kmph"]),
        battery_range_km=int(data["parameters"]["battery_range_km"]),
        charge_minutes=int(data["parameters"]["charge_minutes"]),
        chargers_per_station=int(data["parameters"]["chargers_per_station"]),
    )
    route = [
        RouteSegment(
            start=segment["from"],
            end=segment["to"],
            distance_km=int(segment["distance_km"]),
        )
        for segment in data["route"]
    ]
    buses = [
        Bus(
            bus_id=bus["bus_id"],
            operator=bus["operator"],
            origin=bus["origin"],
            destination=bus["destination"],
            depart_time=bus["depart_time"],
            depart_minute=parse_time_to_minutes(bus["depart_time"]),
        )
        for bus in data["buses"]
    ]
    return Scenario(
        scenario_id=data["scenario_id"],
        weights=weights,
        parameters=parameters,
        route=route,
        stations=list(data["stations"]),
        buses=buses,
    )
```

- [ ] **Step 2: Run scenario tests (expect pass)**

Run: `python -m unittest tests\test_scenario.py -v`  
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add tests\test_scenario.py scheduler\scenario.py
git commit -m "feat: update scenario schema and validation"
```

---

## Self-Review Checklist

- [ ] Spec coverage: tests replaced, schema/validation updated, tests run, commit included.
- [ ] Placeholder scan: no TBD/TODO or vague steps.
- [ ] Type consistency: dataclass fields and load/validation logic match test schema.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-31-scenario-schema-validation.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
