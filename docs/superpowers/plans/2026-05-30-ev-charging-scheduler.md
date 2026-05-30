# EV Charging Scheduler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a data-driven Streamlit app that optimally schedules EV bus charging with CP-SAT and outputs per-bus timelines and per-station charging order.

**Architecture:** Single-process Streamlit UI loads a scenario JSON (route, stations, weights, buses), lets users adjust weights, runs a CP-SAT model, and renders formatted schedule outputs. Core modules handle scenario validation, time modeling, solver construction, and formatting.

**Tech Stack:** Python 3, Streamlit, OR-Tools CP-SAT, unittest (stdlib), pandas (via Streamlit tables)

---

## File structure
- Create: `requirements.txt`
- Create: `app.py`
- Create: `scheduler/__init__.py`
- Create: `scheduler/scenario.py`
- Create: `scheduler/time_model.py`
- Create: `scheduler/solution.py`
- Create: `scheduler/formatting.py`
- Create: `scheduler/solver.py`
- Create: `data/scenarios/scenario_1.json`
- Create: `data/scenarios/scenario_2.json`
- Create: `data/scenarios/scenario_3.json`
- Create: `data/scenarios/scenario_4.json`
- Create: `data/scenarios/scenario_5.json`
- Create: `tests/__init__.py`
- Create: `tests/test_scenario.py`
- Create: `tests/test_time_model.py`
- Create: `tests/test_formatting.py`
- Create: `tests/test_solver.py`
- Create: `README.md`
- Create: `ARCHITECTURE.md`

---

### Task 1: Scaffold project and dependencies

**Files:**
- Create: `requirements.txt`
- Create: `scheduler/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```txt
streamlit
ortools
pandas
```

- [ ] **Step 2: Create package init files**

```python
# scheduler/__init__.py
# Package marker
```

```python
# tests/__init__.py
# Package marker
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt scheduler/__init__.py tests/__init__.py
git commit -m "chore: add dependencies and package scaffolding"
```

---

### Task 2: Scenario model and loader

**Files:**
- Create: `scheduler/scenario.py`
- Create: `tests/test_scenario.py`

- [ ] **Step 1: Write the failing tests**

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
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["A"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "direction": "Bengaluru->Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        scenario = load_scenario(path)

        self.assertEqual(scenario.weights.individual, 1.0)
        self.assertEqual(scenario.buses[0].depart_minute, 570)

    def test_load_scenario_rejects_missing_station(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": [],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "direction": "Bengaluru->Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_scenario -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'scheduler.scenario'`

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path
import json
from typing import List


@dataclass(frozen=True)
class Weights:
    individual: float
    operator: float
    overall: float


@dataclass(frozen=True)
class RouteSegment:
    start: str
    end: str
    distance_km: int


@dataclass(frozen=True)
class Bus:
    bus_id: str
    operator: str
    direction: str
    depart_time: str
    depart_minute: int


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    weights: Weights
    route: List[RouteSegment]
    stations: List[str]
    buses: List[Bus]


def parse_time_to_minutes(value: str) -> int:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {value}")
    hours, minutes = int(parts[0]), int(parts[1])
    return hours * 60 + minutes


def _validate_scenario(data: dict) -> None:
    stations = data.get("stations", [])
    if not stations:
        raise ValueError("Scenario must define at least one station")
    for key in ("weights", "route", "buses"):
        if key not in data:
            raise ValueError(f"Scenario missing '{key}'")


def load_scenario(path: Path) -> Scenario:
    data = json.loads(Path(path).read_text())
    _validate_scenario(data)

    weights = Weights(
        individual=float(data["weights"]["individual"]),
        operator=float(data["weights"]["operator"]),
        overall=float(data["weights"]["overall"]),
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
            direction=bus["direction"],
            depart_time=bus["depart_time"],
            depart_minute=parse_time_to_minutes(bus["depart_time"]),
        )
        for bus in data["buses"]
    ]
    return Scenario(
        scenario_id=data["scenario_id"],
        weights=weights,
        route=route,
        stations=list(data["stations"]),
        buses=buses,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_scenario -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scheduler/scenario.py tests/test_scenario.py
git commit -m "feat: add scenario model and loader"
```

---

### Task 3: Time model helpers

**Files:**
- Create: `scheduler/time_model.py`
- Create: `tests/test_time_model.py`

- [ ] **Step 1: Write the failing tests**

```python
import unittest

from scheduler.scenario import RouteSegment
from scheduler.time_model import (
    distance_to_minutes,
    station_positions,
    travel_minutes_between,
)


class TimeModelTests(unittest.TestCase):
    def test_distance_to_minutes(self):
        self.assertEqual(distance_to_minutes(120, speed_kmph=60), 120)

    def test_station_positions_and_travel(self):
        route = [
            RouteSegment("Bengaluru", "A", 100),
            RouteSegment("A", "B", 120),
            RouteSegment("B", "C", 100),
        ]
        positions = station_positions(route)
        self.assertEqual(positions["A"], 100)
        self.assertEqual(positions["C"], 320)
        self.assertEqual(travel_minutes_between(positions, "A", "C", 60), 220)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_time_model -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'scheduler.time_model'`

- [ ] **Step 3: Write minimal implementation**

```python
from typing import Dict, List

from .scenario import RouteSegment


def distance_to_minutes(distance_km: int, speed_kmph: int = 60) -> int:
    return int(distance_km / speed_kmph * 60)


def station_positions(route: List[RouteSegment]) -> Dict[str, int]:
    positions: Dict[str, int] = {}
    distance = 0
    if not route:
        return positions
    positions[route[0].start] = 0
    for segment in route:
        distance += segment.distance_km
        positions[segment.end] = distance
    return positions


def travel_minutes_between(
    positions: Dict[str, int],
    start: str,
    end: str,
    speed_kmph: int = 60,
) -> int:
    distance = abs(positions[end] - positions[start])
    return distance_to_minutes(distance, speed_kmph=speed_kmph)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_time_model -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scheduler/time_model.py tests/test_time_model.py
git commit -m "feat: add time modeling helpers"
```

---

### Task 4: Solution models and formatting helpers

**Files:**
- Create: `scheduler/solution.py`
- Create: `scheduler/formatting.py`
- Create: `tests/test_formatting.py`

- [ ] **Step 1: Write the failing tests**

```python
import unittest

from scheduler.solution import Solution, TimelineEvent, StationCharge
from scheduler.formatting import timeline_rows, station_order_rows


class FormattingTests(unittest.TestCase):
    def test_formatting_outputs_rows(self):
        solution = Solution(
            status="OPTIMAL",
            bus_events=[
                TimelineEvent(
                    bus_id="bus-1",
                    operator="kpn",
                    event_type="travel",
                    start_minute=0,
                    end_minute=100,
                    station=None,
                ),
                TimelineEvent(
                    bus_id="bus-1",
                    operator="kpn",
                    event_type="charge",
                    start_minute=100,
                    end_minute=125,
                    station="A",
                ),
            ],
            station_events=[
                StationCharge(
                    station="A",
                    bus_id="bus-1",
                    operator="kpn",
                    start_minute=100,
                    end_minute=125,
                )
            ],
            objective={"individual": 0, "operator": 0, "overall": 0},
        )

        timeline = timeline_rows(solution)
        station_rows = station_order_rows(solution)

        self.assertEqual(timeline[0]["event_type"], "travel")
        self.assertEqual(station_rows[0]["station"], "A")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_formatting -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'scheduler.solution'`

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class TimelineEvent:
    bus_id: str
    operator: str
    event_type: str
    start_minute: int
    end_minute: int
    station: Optional[str]


@dataclass(frozen=True)
class StationCharge:
    station: str
    bus_id: str
    operator: str
    start_minute: int
    end_minute: int


@dataclass(frozen=True)
class Solution:
    status: str
    bus_events: List[TimelineEvent]
    station_events: List[StationCharge]
    objective: Dict[str, int]
```

```python
from typing import Dict, List

from .solution import Solution


def timeline_rows(solution: Solution) -> List[Dict[str, object]]:
    return [
        {
            "bus_id": event.bus_id,
            "operator": event.operator,
            "event_type": event.event_type,
            "start_minute": event.start_minute,
            "end_minute": event.end_minute,
            "station": event.station or "",
        }
        for event in solution.bus_events
    ]


def station_order_rows(solution: Solution) -> List[Dict[str, object]]:
    return [
        {
            "station": event.station,
            "bus_id": event.bus_id,
            "operator": event.operator,
            "start_minute": event.start_minute,
            "end_minute": event.end_minute,
        }
        for event in solution.station_events
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_formatting -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scheduler/solution.py scheduler/formatting.py tests/test_formatting.py
git commit -m "feat: add solution models and formatting"
```

---

### Task 5: CP-SAT solver

**Files:**
- Create: `scheduler/solver.py`
- Create: `tests/test_solver.py`

- [ ] **Step 1: Write the failing tests**

```python
import unittest

from scheduler.scenario import Scenario, Weights, RouteSegment, Bus
from scheduler.solver import solve_schedule


class SolverTests(unittest.TestCase):
    def test_solver_returns_solution(self):
        scenario = Scenario(
            scenario_id="test",
            weights=Weights(1.0, 1.0, 1.0),
            route=[
                RouteSegment("Bengaluru", "A", 100),
                RouteSegment("A", "B", 120),
                RouteSegment("B", "C", 100),
                RouteSegment("C", "D", 120),
                RouteSegment("D", "Kochi", 100),
            ],
            stations=["A", "B", "C", "D"],
            buses=[
                Bus(
                    bus_id="bus-1",
                    operator="kpn",
                    direction="Bengaluru->Kochi",
                    depart_time="19:00",
                    depart_minute=19 * 60,
                )
            ],
        )

        solution = solve_schedule(scenario, scenario.weights, time_limit_sec=3)

        self.assertIn(solution.status, {"OPTIMAL", "FEASIBLE"})
        self.assertGreaterEqual(len(solution.station_events), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_solver -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'scheduler.solver'`

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model

from .scenario import Scenario, Weights
from .time_model import station_positions, travel_minutes_between
from .solution import Solution, TimelineEvent, StationCharge


def _ordered_stations(stations: List[str], direction: str) -> List[str]:
    if direction.startswith("Bengaluru"):
        return stations
    return list(reversed(stations))


def _origin_destination(direction: str) -> Tuple[str, str]:
    if direction.startswith("Bengaluru"):
        return "Bengaluru", "Kochi"
    return "Kochi", "Bengaluru"


def _feasible_patterns(
    ordered: List[str],
    positions: Dict[str, int],
    origin: str,
    destination: str,
    max_range_km: int,
) -> List[List[int]]:
    patterns: List[List[int]] = []
    for pattern in product([0, 1], repeat=len(ordered)):
        charge_points = [origin]
        for station, stop in zip(ordered, pattern):
            if stop:
                charge_points.append(station)
        charge_points.append(destination)
        ok = True
        for a, b in zip(charge_points, charge_points[1:]):
            if abs(positions[b] - positions[a]) > max_range_km:
                ok = False
                break
        if ok:
            patterns.append(list(pattern))
    return patterns


def solve_schedule(
    scenario: Scenario,
    weights: Weights,
    time_limit_sec: int = 5,
) -> Solution:
    model = cp_model.CpModel()
    horizon = 24 * 60
    positions = station_positions(scenario.route)

    station_intervals: Dict[str, List[cp_model.IntervalVar]] = {
        station: [] for station in scenario.stations
    }
    all_bus_events: List[TimelineEvent] = []
    all_station_events: List[StationCharge] = []
    bus_wait_totals: List[cp_model.IntVar] = []
    destination_arrivals: List[cp_model.IntVar] = []
    bus_vars: Dict[str, Dict[str, Dict[str, cp_model.IntVar]]] = {}

    for bus in scenario.buses:
        ordered = _ordered_stations(scenario.stations, bus.direction)
        origin, destination = _origin_destination(bus.direction)

        patterns = _feasible_patterns(
            ordered,
            positions,
            origin,
            destination,
            max_range_km=240,
        )
        pattern_vars = [
            model.NewBoolVar(f"pattern_{bus.bus_id}_{i}")
            for i in range(len(patterns))
        ]
        model.Add(sum(pattern_vars) == 1)

        stop_vars = []
        arrival_vars = []
        start_vars = []
        end_vars = []
        depart_vars = []
        wait_vars = []
        bus_vars[bus.bus_id] = {
            "arrival": {},
            "start": {},
            "end": {},
            "stop": {},
        }

        for idx, station in enumerate(ordered):
            stop = model.NewBoolVar(f"stop_{bus.bus_id}_{station}")
            pattern_sum = sum(
                pattern_vars[p_idx]
                for p_idx, pattern in enumerate(patterns)
                if pattern[idx] == 1
            )
            model.Add(stop == pattern_sum)

            arrival = model.NewIntVar(0, horizon, f"arrival_{bus.bus_id}_{station}")
            start = model.NewIntVar(0, horizon, f"start_{bus.bus_id}_{station}")
            end = model.NewIntVar(0, horizon, f"end_{bus.bus_id}_{station}")
            depart = model.NewIntVar(0, horizon, f"depart_{bus.bus_id}_{station}")
            wait = model.NewIntVar(0, horizon, f"wait_{bus.bus_id}_{station}")

            model.Add(start >= arrival).OnlyEnforceIf(stop)
            model.Add(start == arrival).OnlyEnforceIf(stop.Not())
            model.Add(end == start + 25).OnlyEnforceIf(stop)
            model.Add(end == start).OnlyEnforceIf(stop.Not())
            model.Add(wait == start - arrival)
            model.Add(depart == end).OnlyEnforceIf(stop)
            model.Add(depart == arrival).OnlyEnforceIf(stop.Not())

            interval = model.NewOptionalIntervalVar(
                start, 25, end, stop, f"interval_{bus.bus_id}_{station}"
            )
            station_intervals[station].append(interval)

            stop_vars.append(stop)
            arrival_vars.append(arrival)
            start_vars.append(start)
            end_vars.append(end)
            depart_vars.append(depart)
            wait_vars.append(wait)
            bus_vars[bus.bus_id]["arrival"][station] = arrival
            bus_vars[bus.bus_id]["start"][station] = start
            bus_vars[bus.bus_id]["end"][station] = end
            bus_vars[bus.bus_id]["stop"][station] = stop

        for idx, station in enumerate(ordered):
            if idx == 0:
                travel_minutes = travel_minutes_between(
                    positions, origin, station, 60
                )
                model.Add(arrival_vars[idx] == bus.depart_minute + travel_minutes)
            else:
                prev_station = ordered[idx - 1]
                travel_minutes = travel_minutes_between(
                    positions, prev_station, station, 60
                )
                model.Add(arrival_vars[idx] == depart_vars[idx - 1] + travel_minutes)

        dest_arrival = model.NewIntVar(0, horizon, f"arrive_{bus.bus_id}_dest")
        travel_to_dest = travel_minutes_between(
            positions, ordered[-1], destination, 60
        )
        model.Add(dest_arrival == depart_vars[-1] + travel_to_dest)
        destination_arrivals.append(dest_arrival)

        total_wait = model.NewIntVar(0, horizon, f"total_wait_{bus.bus_id}")
        model.Add(total_wait == sum(wait_vars))
        bus_wait_totals.append(total_wait)

    for station, intervals in station_intervals.items():
        model.AddNoOverlap(intervals)

    operator_waits: Dict[str, cp_model.IntVar] = {}
    for operator in sorted({bus.operator for bus in scenario.buses}):
        wait_sum = model.NewIntVar(0, horizon, f"wait_{operator}")
        operator_waits[operator] = wait_sum
        model.Add(
            wait_sum
            == sum(
                total_wait
                for bus, total_wait in zip(scenario.buses, bus_wait_totals)
                if bus.operator == operator
            )
        )

    max_wait = model.NewIntVar(0, horizon, "max_operator_wait")
    min_wait = model.NewIntVar(0, horizon, "min_operator_wait")
    model.AddMaxEquality(max_wait, list(operator_waits.values()))
    model.AddMinEquality(min_wait, list(operator_waits.values()))
    operator_penalty = model.NewIntVar(0, horizon, "operator_penalty")
    model.Add(operator_penalty == max_wait - min_wait)

    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, destination_arrivals)

    weight_individual = int(weights.individual * 100)
    weight_operator = int(weights.operator * 100)
    weight_overall = int(weights.overall * 100)
    model.Minimize(
        weight_individual * sum(bus_wait_totals)
        + weight_operator * operator_penalty
        + weight_overall * makespan
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_sec)
    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    if status_name not in {"OPTIMAL", "FEASIBLE"}:
        return Solution(status=status_name, bus_events=[], station_events=[], objective={})

    for bus in scenario.buses:
        ordered = _ordered_stations(scenario.stations, bus.direction)
        origin, destination = _origin_destination(bus.direction)

        prev_time = bus.depart_minute
        prev_location = origin

        for station in ordered:
            arrival = int(solver.Value(bus_vars[bus.bus_id]["arrival"][station]))
            start = int(solver.Value(bus_vars[bus.bus_id]["start"][station]))
            end = int(solver.Value(bus_vars[bus.bus_id]["end"][station]))
            stop = int(solver.Value(bus_vars[bus.bus_id]["stop"][station]))

            if arrival > prev_time:
                all_bus_events.append(
                    TimelineEvent(
                        bus_id=bus.bus_id,
                        operator=bus.operator,
                        event_type="travel",
                        start_minute=prev_time,
                        end_minute=arrival,
                        station=None,
                    )
                )
            if stop:
                if start > arrival:
                    all_bus_events.append(
                        TimelineEvent(
                            bus_id=bus.bus_id,
                            operator=bus.operator,
                            event_type="wait",
                            start_minute=arrival,
                            end_minute=start,
                            station=station,
                        )
                    )
                all_bus_events.append(
                    TimelineEvent(
                        bus_id=bus.bus_id,
                        operator=bus.operator,
                        event_type="charge",
                        start_minute=start,
                        end_minute=end,
                        station=station,
                    )
                )
                all_station_events.append(
                    StationCharge(
                        station=station,
                        bus_id=bus.bus_id,
                        operator=bus.operator,
                        start_minute=start,
                        end_minute=end,
                    )
                )
                prev_time = end
                prev_location = station
            else:
                prev_time = arrival
                prev_location = station

        dest_arrival = prev_time + travel_minutes_between(
            positions, prev_location, destination, 60
        )
        all_bus_events.append(
            TimelineEvent(
                bus_id=bus.bus_id,
                operator=bus.operator,
                event_type="travel",
                start_minute=prev_time,
                end_minute=dest_arrival,
                station=None,
            )
        )

    objective = {
        "individual": int(sum(solver.Value(w) for w in bus_wait_totals)),
        "operator": int(solver.Value(operator_penalty)),
        "overall": int(solver.Value(makespan)),
    }
    return Solution(
        status=status_name,
        bus_events=sorted(all_bus_events, key=lambda e: (e.bus_id, e.start_minute)),
        station_events=sorted(all_station_events, key=lambda e: (e.station, e.start_minute)),
        objective=objective,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_solver -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scheduler/solver.py tests/test_solver.py
git commit -m "feat: add CP-SAT solver"
```

---

### Task 6: Scenario JSON files

**Files:**
- Create: `data/scenarios/scenario_1.json`
- Create: `data/scenarios/scenario_2.json`
- Create: `data/scenarios/scenario_3.json`
- Create: `data/scenarios/scenario_4.json`
- Create: `data/scenarios/scenario_5.json`
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Add Scenario 1**

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
    { "bus_id": "bus-BK-01", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:00" },
    { "bus_id": "bus-BK-02", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "19:15" },
    { "bus_id": "bus-BK-03", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "19:30" },
    { "bus_id": "bus-BK-04", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:45" },
    { "bus_id": "bus-BK-05", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "20:00" },
    { "bus_id": "bus-BK-06", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "20:15" },
    { "bus_id": "bus-BK-07", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:30" },
    { "bus_id": "bus-BK-08", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "20:45" },
    { "bus_id": "bus-BK-09", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "21:00" },
    { "bus_id": "bus-BK-10", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "21:15" },
    { "bus_id": "bus-KB-01", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:00" },
    { "bus_id": "bus-KB-02", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:15" },
    { "bus_id": "bus-KB-03", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "19:30" },
    { "bus_id": "bus-KB-04", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:45" },
    { "bus_id": "bus-KB-05", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "20:00" },
    { "bus_id": "bus-KB-06", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "20:15" },
    { "bus_id": "bus-KB-07", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "20:30" },
    { "bus_id": "bus-KB-08", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "20:45" },
    { "bus_id": "bus-KB-09", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "21:00" },
    { "bus_id": "bus-KB-10", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "21:15" }
  ]
}
```

- [ ] **Step 2: Add Scenario 2**

```json
{
  "scenario_id": "scenario_2",
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
    { "bus_id": "bus-BK-01", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:00" },
    { "bus_id": "bus-BK-02", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "19:08" },
    { "bus_id": "bus-BK-03", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "19:16" },
    { "bus_id": "bus-BK-04", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:24" },
    { "bus_id": "bus-BK-05", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "19:32" },
    { "bus_id": "bus-BK-06", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "19:40" },
    { "bus_id": "bus-BK-07", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:48" },
    { "bus_id": "bus-BK-08", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "20:03" },
    { "bus_id": "bus-BK-09", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "20:18" },
    { "bus_id": "bus-BK-10", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:33" },
    { "bus_id": "bus-KB-01", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:00" },
    { "bus_id": "bus-KB-02", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:08" },
    { "bus_id": "bus-KB-03", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "19:16" },
    { "bus_id": "bus-KB-04", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:24" },
    { "bus_id": "bus-KB-05", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:32" },
    { "bus_id": "bus-KB-06", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "19:40" },
    { "bus_id": "bus-KB-07", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:48" },
    { "bus_id": "bus-KB-08", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "20:03" },
    { "bus_id": "bus-KB-09", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "20:18" },
    { "bus_id": "bus-KB-10", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "20:33" }
  ]
}
```

- [ ] **Step 3: Add Scenario 3**

```json
{
  "scenario_id": "scenario_3",
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
    { "bus_id": "bus-BK-01", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:00" },
    { "bus_id": "bus-BK-02", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "19:15" },
    { "bus_id": "bus-BK-03", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "19:30" },
    { "bus_id": "bus-BK-04", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:45" },
    { "bus_id": "bus-BK-05", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "20:00" },
    { "bus_id": "bus-BK-06", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "20:15" },
    { "bus_id": "bus-BK-07", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:30" },
    { "bus_id": "bus-BK-08", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "20:45" },
    { "bus_id": "bus-BK-09", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "21:00" },
    { "bus_id": "bus-BK-10", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "21:15" },
    { "bus_id": "bus-KB-01", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:00" },
    { "bus_id": "bus-KB-02", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:35" },
    { "bus_id": "bus-KB-03", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "20:10" },
    { "bus_id": "bus-KB-04", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "20:45" }
  ]
}
```

- [ ] **Step 4: Add Scenario 4 (operator weight 2.0)**

```json
{
  "scenario_id": "scenario_4",
  "weights": { "individual": 1.0, "operator": 2.0, "overall": 1.0 },
  "route": [
    { "from": "Bengaluru", "to": "A", "distance_km": 100 },
    { "from": "A", "to": "B", "distance_km": 120 },
    { "from": "B", "to": "C", "distance_km": 100 },
    { "from": "C", "to": "D", "distance_km": 120 },
    { "from": "D", "to": "Kochi", "distance_km": 100 }
  ],
  "stations": ["A", "B", "C", "D"],
  "buses": [
    { "bus_id": "bus-BK-01", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:00" },
    { "bus_id": "bus-BK-02", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:15" },
    { "bus_id": "bus-BK-03", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:30" },
    { "bus_id": "bus-BK-04", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:45" },
    { "bus_id": "bus-BK-05", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:00" },
    { "bus_id": "bus-BK-06", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:15" },
    { "bus_id": "bus-BK-07", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:30" },
    { "bus_id": "bus-BK-08", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:45" },
    { "bus_id": "bus-BK-09", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "21:00" },
    { "bus_id": "bus-BK-10", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "21:15" },
    { "bus_id": "bus-KB-01", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:00" },
    { "bus_id": "bus-KB-02", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:15" },
    { "bus_id": "bus-KB-03", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "19:30" },
    { "bus_id": "bus-KB-04", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:45" },
    { "bus_id": "bus-KB-05", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "20:00" },
    { "bus_id": "bus-KB-06", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "20:15" },
    { "bus_id": "bus-KB-07", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "20:30" },
    { "bus_id": "bus-KB-08", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "20:45" },
    { "bus_id": "bus-KB-09", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "21:00" },
    { "bus_id": "bus-KB-10", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "21:15" }
  ]
}
```

- [ ] **Step 5: Add Scenario 5**

```json
{
  "scenario_id": "scenario_5",
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
    { "bus_id": "bus-BK-01", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:00" },
    { "bus_id": "bus-BK-02", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "19:08" },
    { "bus_id": "bus-BK-03", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "19:16" },
    { "bus_id": "bus-BK-04", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:24" },
    { "bus_id": "bus-BK-05", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "19:32" },
    { "bus_id": "bus-BK-06", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "19:40" },
    { "bus_id": "bus-BK-07", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "19:48" },
    { "bus_id": "bus-BK-08", "operator": "freshbus", "direction": "Bengaluru->Kochi", "depart_time": "19:56" },
    { "bus_id": "bus-BK-09", "operator": "flixbus", "direction": "Bengaluru->Kochi", "depart_time": "20:04" },
    { "bus_id": "bus-BK-10", "operator": "kpn", "direction": "Bengaluru->Kochi", "depart_time": "20:12" },
    { "bus_id": "bus-KB-01", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:00" },
    { "bus_id": "bus-KB-02", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:08" },
    { "bus_id": "bus-KB-03", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "19:16" },
    { "bus_id": "bus-KB-04", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:24" },
    { "bus_id": "bus-KB-05", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:32" },
    { "bus_id": "bus-KB-06", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "19:40" },
    { "bus_id": "bus-KB-07", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "19:48" },
    { "bus_id": "bus-KB-08", "operator": "flixbus", "direction": "Kochi->Bengaluru", "depart_time": "19:56" },
    { "bus_id": "bus-KB-09", "operator": "kpn", "direction": "Kochi->Bengaluru", "depart_time": "20:04" },
    { "bus_id": "bus-KB-10", "operator": "freshbus", "direction": "Kochi->Bengaluru", "depart_time": "20:12" }
  ]
}
```

- [ ] **Step 6: Extend loader test to ensure all scenarios load**

```python
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
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m unittest tests.test_scenario -v`  
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add data/scenarios/scenario_*.json tests/test_scenario.py
git commit -m "feat: add scenario data files"
```

---

### Task 7: Streamlit UI

**Files:**
- Create: `app.py`

- [ ] **Step 1: Write minimal app implementation**

```python
from pathlib import Path

import streamlit as st

from scheduler.scenario import load_scenario, Weights
from scheduler.solver import solve_schedule
from scheduler.formatting import timeline_rows, station_order_rows

SCENARIO_DIR = Path("data/scenarios")


def load_scenario_names() -> list[str]:
    return sorted(p.stem for p in SCENARIO_DIR.glob("*.json"))


st.set_page_config(page_title="EV Charging Scheduler", layout="wide")
st.title("EV Charging Scheduler")

scenario_names = load_scenario_names()
scenario_name = st.selectbox("Scenario", scenario_names)

scenario_path = SCENARIO_DIR / f"{scenario_name}.json"
scenario = load_scenario(scenario_path)

st.subheader("Scenario input")
st.table(
    [
        {
            "bus_id": bus.bus_id,
            "operator": bus.operator,
            "direction": bus.direction,
            "depart_time": bus.depart_time,
        }
        for bus in scenario.buses
    ]
)

st.subheader("Weights")
individual = st.slider("Individual weight", 0.0, 5.0, float(scenario.weights.individual), 0.1)
operator = st.slider("Operator weight", 0.0, 5.0, float(scenario.weights.operator), 0.1)
overall = st.slider("Overall weight", 0.0, 5.0, float(scenario.weights.overall), 0.1)

if st.button("Run schedule"):
    weights = Weights(individual=individual, operator=operator, overall=overall)
    solution = solve_schedule(scenario, weights, time_limit_sec=5)
    st.subheader("Solver status")
    st.write(solution.status)

    st.subheader("Per-bus timeline")
    st.table(timeline_rows(solution))

    st.subheader("Per-station charging order")
    st.table(station_order_rows(solution))
```

- [ ] **Step 2: Commit**

```bash
git add app.py
git commit -m "feat: add Streamlit UI"
```

---

### Task 8: Documentation

**Files:**
- Create: `README.md`
- Create: `ARCHITECTURE.md`

- [ ] **Step 1: Write README**

```markdown
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
```

- [ ] **Step 2: Write ARCHITECTURE.md**

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add README.md ARCHITECTURE.md
git commit -m "docs: add README and architecture notes"
```

---

## Plan self-review checklist
- Spec coverage: tasks cover scenario data, solver, UI, outputs, and docs.
- Placeholder scan: no TODO/TBD or vague steps.
- Type consistency: Scenario/Bus/Weights names are consistent across tasks.
