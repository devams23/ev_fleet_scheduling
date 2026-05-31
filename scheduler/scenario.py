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

    @property
    def direction(self) -> str:
        return f"{self.origin}->{self.destination}"


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
