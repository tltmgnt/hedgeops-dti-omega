import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sqlite3

from hedgeops.core import Capacity, Scenario, evaluate
from hedgeops.storage import Store
from hedgeops.audit_manifest import export_manifest
from hedgeops.recovery import check_recovery

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.key = patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": "recovery-test-key"})
        self.key.start()
        self.database = self.temp.name + "/original.sqlite3"
        self.backup = self.temp.name + "/restored.sqlite3"
        self.manifest = self.temp.name + "/manifest.json"
        self.store = Store(self.database)
        self.record = evaluate(Scenario(objective="restore", required_minutes=10,
            capacity=Capacity(100, 10, .1, 1), evidence_verified=False,
            constraints_verified=False))
        self.store.save(self.record)
        export_manifest(self.store, self.manifest)
        self.store.backup_verified(self.backup)

    def tearDown(self):
        self.key.stop()
        self.temp.cleanup()

    def test_restored_snapshot_matches_manifest(self):
        self.assertTrue(check_recovery(self.backup, self.manifest)["integrity_ok"])

    def test_deleted_row_detected_after_restore(self):
        with sqlite3.connect(self.backup) as db:
            db.execute("DELETE FROM decisions")
        self.assertFalse(check_recovery(self.backup, self.manifest)["integrity_ok"])

    def test_missing_database_does_not_create_file(self):
        missing = self.temp.name + "/missing.sqlite3"
        self.assertFalse(check_recovery(missing, self.manifest)["integrity_ok"])
        self.assertFalse(Path(missing).exists())

    def test_cli_success_and_failure_exit_codes(self):
        command = [sys.executable, "-m", "hedgeops.recovery", "--database", self.backup,
                   "--manifest", self.manifest]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        with sqlite3.connect(self.backup) as db:
            db.execute("DELETE FROM decisions")
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)

if __name__ == "__main__":
    unittest.main()
