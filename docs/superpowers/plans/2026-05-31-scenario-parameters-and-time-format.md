# Scenario Parameters & Time Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update scenario schema to use origin/destination plus per-scenario parameters, enforce validation, and render all outputs in HH:MM while the solver consumes scenario parameters.

**Architecture:** Scenario JSON is the single source of truth for operational constants (speed, range, charge time, chargers). The solver derives direction from origin/destination relative to route endpoints and uses scenario parameters to build constraints. Formatting converts internal minutes to HH:MM with a 24-hour wrap for display.

**Tech Stack:** Python 3, Streamlit, OR-Tools CP-SAT, unittest

---

## File Structure

- Modify: `scheduler\scenario.py` — schema, parameters, validation, parsing
- Modify: `scheduler\solver.py` — origin/destination handling, parameterized constraints
- Modify: `scheduler\formatting.py` — HH:MM rendering for outputs
- Modify: `app.py` — scenario input table uses origin/destination
- Modify: `tests\test_scenario.py` — schema/validation tests
- Modify: `tests\test_formatting.py` — time formatting tests
- Modify: `tests\test_solver.py` — solver uses parameters/origin-destination
- Modify: `README.md` — document parameters as single source of truth
- Modify: `ARCHITECTURE.md` — update data model and assumptions

---

### Task 1: Scenario schema + validation (parameters, origin/destination, HH:MM)

**Files:**
- Modify: `tests\test_scenario.py`
- Modify: `scheduler\scenario.py`

- [ ] **Step 1: Update scenario tests to the new schema**

Replace `tests\test_scenario.py` with:

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

- [ ] **Step 3: Update scenario schema + validation**

Update `scheduler\scenario.py` to:

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


_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


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

- [ ] **Step 4: Run scenario tests (expect pass)**

Run: `python -m unittest tests\test_scenario.py -v`  
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add tests\test_scenario.py scheduler\scenario.py
git commit -m "feat: update scenario schema and validation"
```

---

### Task 2: HH:MM output formatting

**Files:**
- Modify: `tests\test_formatting.py`
- Modify: `scheduler\formatting.py`

- [ ] **Step 1: Update formatting tests**

Replace `tests\test_formatting.py` with:

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
                    start_minute=1440,
                    end_minute=1500,
                    station="A",
                ),
            ],
            station_events=[
                StationCharge(
                    station="A",
                    bus_id="bus-1",
                    operator="kpn",
                    start_minute=1440,
                    end_minute=1500,
                )
            ],
            objective={"individual": 0, "operator": 0, "overall": 0},
        )

        timeline = timeline_rows(solution)
        station_rows = station_order_rows(solution)

        self.assertEqual(timeline[0]["event_type"], "travel")
        self.assertEqual(timeline[0]["start_time"], "00:00")
        self.assertEqual(timeline[0]["end_time"], "01:40")
        self.assertEqual(timeline[1]["start_time"], "00:00")
        self.assertEqual(timeline[1]["end_time"], "01:00")
        self.assertEqual(station_rows[0]["station"], "A")
        self.assertEqual(station_rows[0]["start_time"], "00:00")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run formatting tests (expect failure)**

Run: `python -m unittest tests\test_formatting.py -v`  
Expected: FAIL (missing `start_time`/`end_time` keys).

- [ ] **Step 3: Add HH:MM formatting in formatter**

Update `scheduler\formatting.py` to:

```python
from typing import Dict, List

from .solution import Solution


def format_minutes(total_minutes: int) -> str:
    minutes = total_minutes % (24 * 60)
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def timeline_rows(solution: Solution) -> List[Dict[str, object]]:
    return [
        {
            "bus_id": event.bus_id,
            "operator": event.operator,
            "event_type": event.event_type,
            "start_time": format_minutes(event.start_minute),
            "end_time": format_minutes(event.end_minute),
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
            "start_time": format_minutes(event.start_minute),
            "end_time": format_minutes(event.end_minute),
        }
        for event in solution.station_events
    ]
```

- [ ] **Step 4: Run formatting tests (expect pass)**

Run: `python -m unittest tests\test_formatting.py -v`  
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add tests\test_formatting.py scheduler\formatting.py
git commit -m "feat: format output times as HH:MM"
```

---

### Task 3: Solver uses parameters and origin/destination

**Files:**
- Modify: `tests\test_solver.py`
- Modify: `scheduler\solver.py`

- [ ] **Step 1: Update solver tests to new schema + parameter usage**

Replace `tests\test_solver.py` with:

```python
import unittest

from scheduler.scenario import Scenario, Weights, Parameters, RouteSegment, Bus
from scheduler.solver import solve_schedule


class SolverTests(unittest.TestCase):
    def test_solver_returns_solution(self):
        scenario = Scenario(
            scenario_id="test",
            weights=Weights(1.0, 1.0, 1.0),
            parameters=Parameters(
                speed_kmph=60,
                battery_range_km=240,
                charge_minutes=30,
                chargers_per_station=1,
            ),
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
                    origin="Bengaluru",
                    destination="Kochi",
                    depart_time="19:00",
                    depart_minute=19 * 60,
                )
            ],
        )

        solution = solve_schedule(scenario, scenario.weights, time_limit_sec=3)

        self.assertIn(solution.status, {"OPTIMAL", "FEASIBLE"})
        self.assertGreaterEqual(len(solution.station_events), 1)
        for event in solution.station_events:
            self.assertEqual(event.end_minute - event.start_minute, 30)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run solver tests (expect failure)**

Run: `python -m unittest tests\test_solver.py -v`  
Expected: FAIL (solver still expects `direction` and fixed parameters).

- [ ] **Step 3: Update solver to use parameters and origin/destination**

Update `scheduler\solver.py` to:

```python
from itertools import product
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model

from .scenario import Scenario, Weights
from .time_model import station_positions, travel_minutes_between
from .solution import Solution, TimelineEvent, StationCharge


def _route_endpoints(scenario: Scenario) -> Tuple[str, str]:
    if not scenario.route:
        raise ValueError("Scenario route is empty")
    return scenario.route[0].start, scenario.route[-1].end


def _ordered_stations(stations: List[str], origin: str, destination: str, start: str) -> List[str]:
    if origin == start:
        return stations
    return list(reversed(stations))


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
    horizon = 72 * 60
    positions = station_positions(scenario.route)
    route_start, route_end = _route_endpoints(scenario)
    speed_kmph = scenario.parameters.speed_kmph
    max_range_km = scenario.parameters.battery_range_km
    charge_minutes = scenario.parameters.charge_minutes
    chargers_per_station = scenario.parameters.chargers_per_station

    station_intervals: Dict[str, List[cp_model.IntervalVar]] = {
        station: [] for station in scenario.stations
    }
    all_bus_events: List[TimelineEvent] = []
    all_station_events: List[StationCharge] = []
    bus_wait_totals: List[cp_model.IntVar] = []
    destination_arrivals: List[cp_model.IntVar] = []
    bus_vars: Dict[str, Dict[str, Dict[str, cp_model.IntVar]]] = {}

    for bus in scenario.buses:
        ordered = _ordered_stations(
            scenario.stations, bus.origin, bus.destination, route_start
        )
        origin, destination = bus.origin, bus.destination

        patterns = _feasible_patterns(
            ordered,
            positions,
            origin,
            destination,
            max_range_km=max_range_km,
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
            model.Add(end == start + charge_minutes).OnlyEnforceIf(stop)
            model.Add(end == start).OnlyEnforceIf(stop.Not())
            model.Add(wait == start - arrival)
            model.Add(depart == end).OnlyEnforceIf(stop)
            model.Add(depart == arrival).OnlyEnforceIf(stop.Not())

            interval = model.NewOptionalIntervalVar(
                start, charge_minutes, end, stop, f"interval_{bus.bus_id}_{station}"
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
                    positions, origin, station, speed_kmph
                )
                model.Add(arrival_vars[idx] == bus.depart_minute + travel_minutes)
            else:
                prev_station = ordered[idx - 1]
                travel_minutes = travel_minutes_between(
                    positions, prev_station, station, speed_kmph
                )
                model.Add(arrival_vars[idx] == depart_vars[idx - 1] + travel_minutes)

        dest_arrival = model.NewIntVar(0, horizon, f"arrive_{bus.bus_id}_dest")
        travel_to_dest = travel_minutes_between(
            positions, ordered[-1], destination, speed_kmph
        )
        model.Add(dest_arrival == depart_vars[-1] + travel_to_dest)
        destination_arrivals.append(dest_arrival)

        total_wait = model.NewIntVar(0, horizon, f"total_wait_{bus.bus_id}")
        model.Add(total_wait == sum(wait_vars))
        bus_wait_totals.append(total_wait)

    for station, intervals in station_intervals.items():
        if intervals:
            model.AddCumulative(intervals, [1] * len(intervals), chargers_per_station)

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
        ordered = _ordered_stations(
            scenario.stations, bus.origin, bus.destination, route_start
        )
        origin, destination = bus.origin, bus.destination

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
            positions, prev_location, destination, speed_kmph
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

- [ ] **Step 4: Run solver tests (expect pass)**

Run: `python -m unittest tests\test_solver.py -v`  
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add tests\test_solver.py scheduler\solver.py
git commit -m "feat: parameterize solver and use origin/destination"
```

---

### Task 4: UI + docs reflect new schema

**Files:**
- Modify: `app.py`
- Modify: `README.md`
- Modify: `ARCHITECTURE.md`

- [ ] **Step 1: Update scenario input table in the UI**

In `app.py`, replace the scenario table block with:

```python
st.subheader("Scenario input")
st.table(
    [
        {
            "bus_id": bus.bus_id,
            "operator": bus.operator,
            "origin": bus.origin,
            "destination": bus.destination,
            "depart_time": bus.depart_time,
        }
        for bus in scenario.buses
    ]
)
```

- [ ] **Step 2: Update README for parameters + schema**

In `README.md`, update the schema examples:

```markdown
## Change a weight
- Use the sliders in the UI, or edit the `weights` section of a scenario JSON in `data\scenarios\`:
```json
{
  "weights": { "individual": 1.0, "operator": 2.0, "overall": 1.0 }
}
```

## Change a parameter
- Edit the `parameters` section in a scenario JSON (single source of truth):
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
```

- [ ] **Step 3: Update ARCHITECTURE data model + assumptions**

In `ARCHITECTURE.md`, update the JSON example and assumptions to:

```markdown
```json
{
  "scenario_id": "scenario_1",
  "weights": { "individual": 1.0, "operator": 1.0, "overall": 1.0 },
  "parameters": { "speed_kmph": 60, "battery_range_km": 240, "charge_minutes": 25, "chargers_per_station": 1 },
  "route": [
    { "from": "Bengaluru", "to": "A", "distance_km": 100 },
    { "from": "A", "to": "B", "distance_km": 120 }
  ],
  "stations": ["A", "B", "C", "D"],
  "buses": [
    { "bus_id": "bus-BK-01", "operator": "kpn", "origin": "Bengaluru", "destination": "Kochi", "depart_time": "19:00" }
  ]
}
```

## Assumptions
- Speed, range, charge time, and charger count are defined in each scenario's `parameters`.
- One charger per station and no backtracking are defaults that can be changed via data.
```

- [ ] **Step 4: Commit**

```bash
git add app.py README.md ARCHITECTURE.md
git commit -m "docs: reflect parameters and origin/destination schema"
```

---

## Plan Self-Review

- Spec coverage: scenario schema changes, parameters, HH:MM output, validation, and solver parameterization are all addressed in Tasks 1–4.
- Placeholder scan: no TBDs or missing code blocks.
- Type consistency: `Parameters`, `origin`, and `destination` are used consistently across tasks.

