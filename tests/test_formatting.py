import unittest

from scheduler.solution import Solution, TimelineEvent, StationCharge
from scheduler.formatting import (
    format_minutes_hhmm,
    station_order_rows,
    timeline_rows,
)


class FormattingTests(unittest.TestCase):
    def test_format_minutes_hhmm_wraps_24h_clock(self):
        self.assertEqual(format_minutes_hhmm(0), "00:00")
        self.assertEqual(format_minutes_hhmm(100), "01:40")
        self.assertEqual(format_minutes_hhmm(1440), "00:00")

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
                    end_minute=1465,
                    station="A",
                ),
            ],
            station_events=[
                StationCharge(
                    station="A",
                    bus_id="bus-1",
                    operator="kpn",
                    start_minute=1440,
                    end_minute=1465,
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
        self.assertEqual(timeline[1]["end_time"], "00:25")
        self.assertEqual(station_rows[0]["station"], "A")
        self.assertEqual(station_rows[0]["start_time"], "00:00")
        self.assertEqual(station_rows[0]["end_time"], "00:25")


if __name__ == "__main__":
    unittest.main()
