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
