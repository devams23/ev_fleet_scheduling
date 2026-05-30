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
