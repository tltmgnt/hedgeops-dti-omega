import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from hedgeops.core import Capacity, Scenario, evaluate
from hedgeops.storage import Store
from hedgeops.audit_manifest import export_manifest, verify_manifest

class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.key = patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": "test-manifest-secret"})
        self.key.start()
        self.store = Store(self.temp.name + "/records.sqlite3")
        self.path = self.temp.name + "/manifest.json"
        self.record = evaluate(Scenario(objective="manifest review", required_minutes=10,
            capacity=Capacity(100, 10, .1, 1), evidence_verified=False,
            constraints_verified=False))
        self.store.save(self.record)

    def tearDown(self):
        self.key.stop()
        self.temp.cleanup()

    def test_manifest_roundtrip(self):
        export_manifest(self.store, self.path)
        self.assertTrue(verify_manifest(self.store, self.path)["integrity_ok"])

    def test_deletion_detected(self):
        export_manifest(self.store, self.path)
        with sqlite3.connect(self.store.path) as db:
            db.execute("DELETE FROM decisions")
        result = verify_manifest(self.store, self.path)
        self.assertFalse(result["integrity_ok"])
        self.assertEqual(result["actual_count"], 0)

    def test_manifest_tampering_detected(self):
        export_manifest(self.store, self.path)
        manifest = json.loads(Path(self.path).read_text())
        manifest["count"] = 0
        Path(self.path).write_text(json.dumps(manifest))
        self.assertEqual(verify_manifest(self.store, self.path)["reason"], "invalid signature")

    def test_wrong_key_detected(self):
        export_manifest(self.store, self.path)
        with patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": "wrong-key"}):
            wrong_store = Store(self.store.path)
            self.assertFalse(verify_manifest(wrong_store, self.path)["integrity_ok"])

    def test_manifest_never_overwritten(self):
        export_manifest(self.store, self.path)
        with self.assertRaises(FileExistsError):
            export_manifest(self.store, self.path)

if __name__ == "__main__":
    unittest.main()
