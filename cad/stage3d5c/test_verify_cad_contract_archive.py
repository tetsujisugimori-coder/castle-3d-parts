"""Regression: a ZIP-like source tree missing 30 hidden entries must FAIL."""
import hashlib
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

from verify_cad_contract_archive import VerificationError, audit


class ContractArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
            subprocess.run(["git", "-C", str(self.repo), "config", key, value], check=True)
        paths = ["regular.txt"] + [f".github/workflows/hidden-{i:02d}.yml"
                                   for i in range(30)]
        for name in paths:
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(name + "\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "fixture"], check=True)
        self.artifact = self.root / "artifact"
        self.source = self.artifact / "source"
        self.source.mkdir(parents=True)
        data = subprocess.check_output(["git", "-C", str(self.repo), "archive", "HEAD"])
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tar:
            tar.extractall(self.source, filter="data")
        rows = []
        for name in paths:
            sha = hashlib.sha256((self.repo / name).read_bytes()).hexdigest()
            rows.append(f"{sha}  {name}\n")
        (self.artifact / "manifest.sha256").write_text("".join(rows), encoding="utf-8")

    def test_full_set_passes_and_counts_hidden(self):
        result = audit(self.repo, self.artifact)
        self.assertEqual((result["expected_count"], result["hidden_count"]), (31, 30))
        self.assertEqual(result["status"], "PASS")

    def test_historical_hidden_thirty_omission_rejected(self):
        for item in (self.source / ".github/workflows").iterdir():
            item.unlink()
        with self.assertRaisesRegex(VerificationError, '"count": 30'):
            audit(self.repo, self.artifact)

    def test_one_nonhidden_missing_rejected(self):
        (self.source / "regular.txt").unlink()
        with self.assertRaisesRegex(VerificationError, "SOURCE_SET_MISMATCH"):
            audit(self.repo, self.artifact)

    def test_payload_byte_mutation_rejected(self):
        (self.source / "regular.txt").write_bytes(b"tampered")
        with self.assertRaisesRegex(VerificationError, "altered"):
            audit(self.repo, self.artifact)

    def test_extra_file_rejected(self):
        (self.source / "extra.txt").write_bytes(b"extra")
        with self.assertRaisesRegex(VerificationError, "extra"):
            audit(self.repo, self.artifact)

    def test_manifest_wrong_hash_rejected(self):
        path = self.artifact / "manifest.sha256"
        path.write_text(path.read_text().replace("a", "b", 1))
        with self.assertRaises(VerificationError):
            audit(self.repo, self.artifact)

    def test_manifest_missing_hidden_rejected(self):
        path = self.artifact / "manifest.sha256"
        lines = path.read_text().splitlines(keepends=True)
        path.write_text(lines[0], encoding="utf-8")
        with self.assertRaisesRegex(VerificationError, "manifest_missing"):
            audit(self.repo, self.artifact)

    def test_invalid_prior_rejected(self):
        prior = self.artifact / "prior.json"
        prior.write_text('{"status":"PASS","expected_count":0}\n', encoding="utf-8")
        with self.assertRaisesRegex(VerificationError, "pre-upload audit"):
            audit(self.repo, self.artifact, prior)


if __name__ == "__main__":
    unittest.main()
