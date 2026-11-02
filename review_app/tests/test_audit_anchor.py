import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hedgeops.audit_anchor import check_anchor
from hedgeops.audit_manifest import export_manifest
from hedgeops.storage import Store


class AuditAnchorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        key_patch = patch.dict(os.environ, {"HEDGEOPS_AUDIT_KEY": "test-only-anchor-key"})
        key_patch.start()
        self.addCleanup(key_patch.stop)
        self.store = Store(self.folder / "audit.sqlite3")
        self.manifest = self.folder / "manifest.json"
        export_manifest(self.store, self.manifest)
        self.digest = hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def test_matching_anchor_and_manifest(self):
        result = check_anchor(self.store.path, self.manifest, self.digest)
        self.assertTrue(result["integrity_ok"])

    def test_wrong_anchor_rejected(self):
        result = check_anchor(self.store.path, self.manifest, "0" * 64)
        self.assertFalse(result["integrity_ok"])

    def test_tampered_manifest_rejected(self):
        data = json.loads(self.manifest.read_text())
        data["count"] = 10
        self.manifest.write_text(json.dumps(data))
        result = check_anchor(self.store.path, self.manifest, self.digest)
        self.assertFalse(result["integrity_ok"])

    def test_invalid_digest_format_rejected(self):
        for digest in ("", "A" * 64, "z" * 64, "123"):
            with self.subTest(digest=digest):
                with self.assertRaises(ValueError):
                    check_anchor(self.store.path, self.manifest, digest)

    def test_missing_manifest_rejected(self):
        with self.assertRaises(FileNotFoundError):
            check_anchor(self.store.path, self.folder / "missing.json", self.digest)


if __name__ == "__main__":
    unittest.main()
