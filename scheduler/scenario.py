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
