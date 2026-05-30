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
