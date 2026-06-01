from typing import Dict, List

from .solution_model import Solution


def format_minutes_hhmm(total_minutes: int) -> str:
    wrapped_minutes = total_minutes % (24 * 60)
    hours = wrapped_minutes // 60
    minutes = wrapped_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def timeline_rows(solution: Solution) -> List[Dict[str, object]]:
    return [
        {
            "bus_id": event.bus_id,
            "operator": event.operator,
            "event_type": event.event_type,
            "start_time": format_minutes_hhmm(event.start_minute),
            "end_time": format_minutes_hhmm(event.end_minute),
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
            "start_time": format_minutes_hhmm(event.start_minute),
            "end_time": format_minutes_hhmm(event.end_minute),
        }
        for event in solution.station_events
    ]
