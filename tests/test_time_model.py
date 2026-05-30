import unittest

from scheduler.scenario import RouteSegment
from scheduler.time_model import (
    distance_to_minutes,
    station_positions,
    travel_minutes_between,
)


class TimeModelTests(unittest.TestCase):
    def test_distance_to_minutes(self):
        self.assertEqual(distance_to_minutes(120, speed_kmph=60), 120)

    def test_station_positions_and_travel(self):
        route = [
            RouteSegment("Bengaluru", "A", 100),
            RouteSegment("A", "B", 120),
            RouteSegment("B", "C", 100),
        ]
        positions = station_positions(route)
        self.assertEqual(positions["A"], 100)
        self.assertEqual(positions["C"], 320)
        self.assertEqual(travel_minutes_between(positions, "A", "C", 60), 220)


if __name__ == "__main__":
    unittest.main()
