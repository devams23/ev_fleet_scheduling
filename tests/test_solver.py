import unittest

from scheduler.scenario import Scenario, Weights, RouteSegment, Bus
from scheduler.solver import solve_schedule


class SolverTests(unittest.TestCase):
    def test_solver_returns_solution(self):
        scenario = Scenario(
            scenario_id="test",
            weights=Weights(1.0, 1.0, 1.0),
            route=[
                RouteSegment("Bengaluru", "A", 100),
                RouteSegment("A", "B", 120),
                RouteSegment("B", "C", 100),
                RouteSegment("C", "D", 120),
                RouteSegment("D", "Kochi", 100),
            ],
            stations=["A", "B", "C", "D"],
            buses=[
                Bus(
                    bus_id="bus-1",
                    operator="kpn",
                    direction="Bengaluru->Kochi",
                    depart_time="19:00",
                    depart_minute=19 * 60,
                )
            ],
        )

        solution = solve_schedule(scenario, scenario.weights, time_limit_sec=3)

        self.assertIn(solution.status, {"OPTIMAL", "FEASIBLE"})
        self.assertGreaterEqual(len(solution.station_events), 1)


if __name__ == "__main__":
    unittest.main()
