import json
import tempfile
import unittest
from pathlib import Path

from scheduler.scenario import load_scenario


class ScenarioTests(unittest.TestCase):
    def _write_temp_scenario(self, data: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(data, tmp)
        tmp.close()
        return Path(tmp.name)

    def test_load_scenario_parses_times_and_weights(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["A"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        scenario = load_scenario(path)

        self.assertEqual(scenario.weights.individual, 1.0)
        self.assertEqual(scenario.parameters.battery_range_km, 240)
        self.assertEqual(scenario.buses[0].depart_minute, 570)
        self.assertEqual(scenario.buses[0].origin, "Bengaluru")

    def test_load_scenario_rejects_missing_station(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": [],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)

    def test_load_scenario_rejects_bad_time_format(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["A"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "9:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)

    def test_load_scenario_rejects_station_mismatch(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "parameters": {
                    "speed_kmph": 60,
                    "battery_range_km": 240,
                    "charge_minutes": 25,
                    "chargers_per_station": 1,
                },
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["B"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "origin": "Bengaluru",
                        "destination": "Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)

    def test_all_scenarios_load(self):
        for name in [
            "data/scenarios/scenario_1.json",
            "data/scenarios/scenario_2.json",
            "data/scenarios/scenario_3.json",
            "data/scenarios/scenario_4.json",
            "data/scenarios/scenario_5.json",
        ]:
            scenario = load_scenario(name)
            self.assertGreaterEqual(len(scenario.buses), 4)


if __name__ == "__main__":
    unittest.main()
