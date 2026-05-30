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
