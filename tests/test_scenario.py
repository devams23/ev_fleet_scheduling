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
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": ["A"],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "direction": "Bengaluru->Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        scenario = load_scenario(path)

        self.assertEqual(scenario.weights.individual, 1.0)
        self.assertEqual(scenario.buses[0].depart_minute, 570)

    def test_load_scenario_rejects_missing_station(self):
        path = self._write_temp_scenario(
            {
                "scenario_id": "test",
                "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0},
                "route": [
                    {"from": "Bengaluru", "to": "A", "distance_km": 100},
                    {"from": "A", "to": "Kochi", "distance_km": 100},
                ],
                "stations": [],
                "buses": [
                    {
                        "bus_id": "bus-1",
                        "operator": "kpn",
                        "direction": "Bengaluru->Kochi",
                        "depart_time": "09:30",
                    }
                ],
            }
        )

        with self.assertRaises(ValueError):
            load_scenario(path)


if __name__ == "__main__":
    unittest.main()
