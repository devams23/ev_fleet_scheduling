from itertools import product
from typing import Dict, List

from ortools.sat.python import cp_model

from .scenario import Scenario, Weights
from .time_model import station_positions, travel_minutes_between
from .solution_model import Solution, TimelineEvent, StationCharge


def _ordered_stations(
    stations: List[str],
    route_start: str,
    route_end: str,
    origin: str,
    destination: str,
) -> List[str]:
    if origin == route_start and destination == route_end:
        return stations
    if origin == route_end and destination == route_start:
        return list(reversed(stations))
    raise ValueError("Bus origin/destination must match route endpoints")


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
    speed_kmph = scenario.parameters.speed_kmph
    battery_range_km = scenario.parameters.battery_range_km
    charge_minutes = scenario.parameters.charge_minutes
    chargers_per_station = scenario.parameters.chargers_per_station
    if speed_kmph <= 0:
        raise ValueError("speed_kmph must be > 0")
    if battery_range_km <= 0:
        raise ValueError("battery_range_km must be > 0")
    if charge_minutes <= 0:
        raise ValueError("charge_minutes must be > 0")
    if chargers_per_station <= 0:
        raise ValueError("chargers_per_station must be > 0")

    model = cp_model.CpModel()
    horizon = 72 * 60
    positions = station_positions(scenario.route)
    route_start = scenario.route[0].start
    route_end = scenario.route[-1].end

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
            scenario.stations, route_start, route_end, bus.origin, bus.destination
        )
        origin, destination = bus.origin, bus.destination

        patterns = _feasible_patterns(
            ordered,
            positions,
            origin,
            destination,
            max_range_km=battery_range_km,
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
        if chargers_per_station <= 1:
            model.AddNoOverlap(intervals)
        else:
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
            scenario.stations, route_start, route_end, bus.origin, bus.destination
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
