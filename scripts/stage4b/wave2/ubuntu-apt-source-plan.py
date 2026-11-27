"""Identify standalone Microsoft prod apt sources unused by this Playwright job."""
from pathlib import Path
import re
import sys

MICROSOFT = "https://packages.microsoft.com/ubuntu/24.04/prod"


def plan(directory):
    for source in sorted(directory.iterdir()):
        if source.suffix not in (".list", ".sources") or not source.is_file():
            continue
        active = "\n".join(x.split("#", 1)[0] for x in source.read_text().splitlines())
        urls = {x.rstrip("/") for x in re.findall(r"https?://[^\s]+", active)}
        if MICROSOFT not in urls:
            continue
        if urls != {MICROSOFT} or source.is_symlink() or not re.fullmatch(r"[a-zA-Z0-9_.-]+", source.name):
            raise ValueError("refusing to omit a shared or aliased apt source: " + source.name)
        yield source.name


if __name__ == "__main__":
    for path in plan(Path(sys.argv[1])):
        print(path)
