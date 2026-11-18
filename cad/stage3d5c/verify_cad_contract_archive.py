"""Fail closed on CAD contract source loss, including dot-prefixed paths.

Pre-upload and downloaded-artifact verification use Git HEAD's *actual* tree
(via git archive), not a self-reported manifest or a reconstructed old ZIP.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile


class VerificationError(Exception):
    pass


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_paths(repo):
    archive = git(repo, "archive", "HEAD")
    expected = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        for member in tar:
            if member.isdir():
                continue
            if not member.isfile():
                raise VerificationError(f"unsupported git entry: {member.name}")
            name = member.name
            if name in expected or name.startswith("/") or ".." in Path(name).parts:
                raise VerificationError(f"duplicate/unsafe git entry: {name}")
            handle = tar.extractfile(member)
            if handle is None:
                raise VerificationError(f"unreadable git entry: {name}")
            data = handle.read()
            expected[name] = {"bytes": len(data), "sha256": digest(data)}
    return expected


def is_hidden(path):
    return any(part.startswith(".") for part in path.split("/"))


def audit(repo, artifact_dir, prior=None):
    repo = Path(repo).resolve()
    artifact_dir = Path(artifact_dir).resolve()
    expected = checked_paths(repo)
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    tree = git(repo, "rev-parse", "HEAD^{tree}").decode().strip()
    source = artifact_dir / "source"
    manifest = artifact_dir / "manifest.sha256"
    if not source.is_dir() or not manifest.is_file():
        raise VerificationError("missing source/ or manifest.sha256")
    actual = {}
    for path in source.rglob("*"):
        if path.is_symlink():
            raise VerificationError(f"symlink in artifact source: {path}")
        if path.is_file():
            name = path.relative_to(source).as_posix()
            data = path.read_bytes()
            actual[name] = {"bytes": len(data), "sha256": digest(data)}
    listed = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise VerificationError("invalid manifest.sha256 record")
        sha, path = match.groups()
        if path in listed:
            raise VerificationError(f"duplicate manifest path: {path}")
        listed[path] = sha
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    altered = sorted(path for path in set(expected) & set(actual)
                     if actual[path] != expected[path])
    manifest_missing = sorted(set(expected) - set(listed))
    manifest_extra = sorted(set(listed) - set(expected))
    manifest_wrong = sorted(path for path in set(expected) & set(listed)
                            if listed[path] != expected[path]["sha256"])
    problems = {
        "missing": missing, "extra": extra, "altered": altered,
        "manifest_missing": manifest_missing, "manifest_extra": manifest_extra,
        "manifest_wrong": manifest_wrong,
    }
    if any(problems.values()):
        raise VerificationError("SOURCE_SET_MISMATCH " + json.dumps(
            {key: {"count": len(value), "first": value[:5]}
             for key, value in problems.items() if value}, sort_keys=True))
    rows = "".join(f"{path}\0{expected[path]['bytes']}\0{expected[path]['sha256']}\n"
                   for path in sorted(expected))
    report = {
        "status": "PASS",
        "head": head,
        "tree": tree,
        "expected_count": len(expected),
        "hidden_count": sum(is_hidden(p) for p in expected),
        "source_count": len(actual),
        "manifest_count": len(listed),
        "root_digest": digest(rows.encode("utf-8")),
        "coverage": "exact git archive HEAD source, including hidden paths",
    }
    if prior is not None:
        previous = json.loads(Path(prior).read_text(encoding="utf-8"))
        keys = ("status", "head", "tree", "expected_count", "hidden_count",
                "source_count", "manifest_count", "root_digest")
        if any(previous.get(key) != report[key] for key in keys):
            raise VerificationError("pre-upload audit identity/count/digest mismatch")
        report["compared_with_pre_upload"] = True
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit(args.repo, args.artifact_dir, args.prior)
        exit_code = 0
    except (VerificationError, subprocess.CalledProcessError, OSError,
            ValueError, tarfile.TarError) as exc:
        report = {"status": "FAIL", "reason": str(exc)}
        exit_code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True,
                                      indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
