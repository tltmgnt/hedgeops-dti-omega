import tempfile
import unittest
from hedgeops.core import Capacity, Scenario, evaluate, from_dict, simulate
from hedgeops.storage import Store

class ReviewTests(unittest.TestCase):
    def scenario(self, **changes):
        args = dict(objective="Review", required_minutes=30, capacity=Capacity(120, 20, .1, 1),
                    expected_value=100, downside_exposure=10, max_downside=20,
                    evidence_verified=True, constraints_verified=True)
        args.update(changes)
        return Scenario(**args)

    def test_capacity_proxy(self):
        self.assertAlmostEqual(Capacity(100, 20, .25, .5, 10).effective_minutes, 26.25)

    def test_all_six_roles_and_no_execution(self):
        record = evaluate(self.scenario())
        self.assertEqual({a["agent"] for a in record["assessments"]}, {
            "economic", "statistical", "machine_learning", "behavioral", "risk", "arbitration"})
        self.assertFalse(record["execution_authorized"])
        self.assertEqual(record["status"], "needs_review")

    def test_constraints_block(self):
        self.assertEqual(evaluate(self.scenario(required_minutes=500))["status"], "blocked")
        self.assertEqual(evaluate(self.scenario(downside_exposure=30))["status"], "blocked")
        self.assertEqual(evaluate(self.scenario(evidence_verified=False))["status"], "blocked")

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError): Capacity(100, 101, 0, 1)
        with self.assertRaises(ValueError): Capacity(100, 0, float("nan"), 1)
        with self.assertRaises(ValueError): from_dict({"objective":"x", "capacity": {"horizon_minutes":100,
            "committed_minutes":0,"fragmentation_index":0,"autonomy_fraction":1},"evidence_verified":1})

    def test_simulation(self):
        self.assertEqual(len(simulate(self.scenario())), 5)

    def test_storage_and_audit(self):
        with tempfile.TemporaryDirectory() as path:
            store = Store(path + "/review.sqlite3")
            record = evaluate(self.scenario())
            store.save(record)
            self.assertEqual(store.get(record["record_id"])["record_id"], record["record_id"])
            self.assertEqual(len(store.list(1)), 1)
            self.assertTrue(store.verify()["integrity_ok"])


    def test_required_field_validation(self):
        with self.assertRaisesRegex(ValueError, "required_minutes"):
            from_dict({"objective": "Missing time", "capacity": {
                "horizon_minutes": 100, "committed_minutes": 0,
                "fragmentation_index": 0, "autonomy_fraction": 1}})
        with self.assertRaisesRegex(ValueError, "autonomy_fraction"):
            from_dict({"objective": "Missing capacity", "required_minutes": 10,
                       "capacity": {"horizon_minutes": 100, "committed_minutes": 0,
                                    "fragmentation_index": 0}})

    def test_unknown_fields_and_nonfinite_values(self):
        from dataclasses import asdict
        data = asdict(self.scenario())
        data["unknown"] = "unexpected"
        with self.assertRaises(ValueError):
            from_dict(data)
        data.pop("unknown")
        data["uncertainty"] = float("inf")
        with self.assertRaises(ValueError):
            from_dict(data)

    def test_unverified_constraints_never_authorize_execution(self):
        record = evaluate(self.scenario(constraints_verified=False))
        self.assertTrue(record["human_approval_required"])
        self.assertFalse(record["execution_authorized"])
        self.assertIn("UNVERIFIED_CONSTRAINTS", {flag["code"] for flag in record["risk_flags"]})

    def test_audit_detects_tampering(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as path:
            store = Store(path + "/review.sqlite3")
            record = evaluate(self.scenario())
            store.save(record)
            with sqlite3.connect(store.path) as db:
                db.execute("UPDATE decisions SET payload=? WHERE id=?",
                           ('{"modified":true}', record["record_id"]))
            result = store.verify()
            self.assertFalse(result["integrity_ok"])
            self.assertIn(record["record_id"], result["invalid_ids"])

    def test_history_limit_validation(self):
        with tempfile.TemporaryDirectory() as path:
            store = Store(path + "/review.sqlite3")
            for limit in (0, -1, 101, 1.5, True):
                with self.subTest(limit=limit), self.assertRaises(ValueError):
                    store.list(limit)


    def test_shared_contract_accepts_review_result(self):
        from hedgeops.contract import normalize
        record = evaluate(self.scenario())
        summary = normalize(record)
        self.assertEqual(summary.status, "needs_review")
        self.assertFalse(summary.execution_authorized)

    def test_shared_contract_rejects_executable_record(self):
        from hedgeops.contract import normalize
        record = evaluate(self.scenario())
        record["execution_authorized"] = True
        with self.assertRaises(ValueError):
            normalize(record)


    def test_verified_backup_restores_records(self):
        with tempfile.TemporaryDirectory() as path:
            store = Store(path + "/source.sqlite3")
            record = evaluate(self.scenario())
            store.save(record)
            backup = path + "/snapshot.sqlite3"
            self.assertEqual(store.backup_verified(backup), backup)
            restored = Store(backup)
            self.assertTrue(restored.verify()["integrity_ok"])
            self.assertEqual(restored.get(record["record_id"]), record)
            with self.assertRaises(FileExistsError):
                store.backup_verified(backup)

    def test_backup_refuses_tampered_source(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as path:
            store = Store(path + "/source.sqlite3")
            record = evaluate(self.scenario())
            store.save(record)
            with sqlite3.connect(store.path) as db:
                db.execute("UPDATE decisions SET payload=? WHERE id=?",
                           ('{"tampered":true}', record["record_id"]))
            with self.assertRaisesRegex(ValueError, "integrity failed"):
                store.backup_verified(path + "/snapshot.sqlite3")


    def test_keyed_audit_detects_database_rewrite(self):
        import os
        import sqlite3
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as path:
            with patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": "external-test-key"}):
                store = Store(path + "/keyed.sqlite3")
                record = evaluate(self.scenario())
                store.save(record)
                self.assertTrue(store.verify()["integrity_ok"])
                with sqlite3.connect(store.path) as db:
                    db.execute("UPDATE decisions SET payload=? WHERE id=?",
                               ('{"tampered":true}', record["record_id"]))
                self.assertIn(record["record_id"], store.verify()["invalid_ids"])

    def test_keyed_audit_rejects_wrong_or_missing_key(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as path:
            with patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": "correct-key"}):
                store = Store(path + "/keyed.sqlite3")
                store.save(evaluate(self.scenario()))
            for key in ("wrong-key", ""):
                with self.subTest(key=key), patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": key}):
                    self.assertFalse(Store(store.path).verify()["integrity_ok"])

    def test_keyed_mode_flags_legacy_unkeyed_records(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as path:
            with patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": ""}):
                store = Store(path + "/mixed.sqlite3")
                store.save(evaluate(self.scenario()))
            with patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": "external-test-key"}):
                result = Store(store.path).verify()
                self.assertFalse(result["integrity_ok"])
                self.assertEqual(len(result["unverified_legacy_ids"]), 1)

if __name__ == "__main__":
    unittest.main()
