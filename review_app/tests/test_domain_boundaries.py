import unittest
from hedgeops.core import Capacity, Scenario, evaluate, simulate

class DomainBoundaryTests(unittest.TestCase):
    def test_fragmentation_monotonic(self):
        values = [Capacity(120, 20, f, .8, 10).effective_minutes for f in (0, .01, .25, .5, .99, 1)]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertGreaterEqual(values[-1], 0)

    def test_recovery_overhead_monotonic(self):
        values = [Capacity(100, 20, .2, 1, r).effective_minutes for r in (0, 1, 20, 80, 120)]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(values[-1], 0)

    def test_exact_capacity_boundary_remains_review_only(self):
        cap = Capacity(100, 20, 0, 1)
        def record(required):
            return evaluate(Scenario(objective="boundary", required_minutes=required,
                                    capacity=cap, evidence_verified=True, constraints_verified=True))
        self.assertEqual(record(80)["status"], "needs_review")
        self.assertEqual(record(80.0001)["status"], "blocked")
        self.assertFalse(record(80)["execution_authorized"])

    def test_simulated_feasibility_monotonic(self):
        scenario = Scenario(objective="simulation", required_minutes=50,
                            capacity=Capacity(100, 10, 0, 1))
        results = simulate(scenario, (0, .25, .5, .75, 1))
        flags = [item["feasible"] for item in results]
        self.assertEqual(flags, sorted(flags, reverse=True))

    def test_downside_boundary(self):
        common = dict(objective="risk", required_minutes=1,
                      capacity=Capacity(100, 0, 0, 1), max_downside=10,
                      evidence_verified=True, constraints_verified=True)
        self.assertEqual(evaluate(Scenario(**common, downside_exposure=10))["status"], "needs_review")
        self.assertEqual(evaluate(Scenario(**common, downside_exposure=10.0001))["status"], "blocked")

if __name__ == "__main__":
    unittest.main()
