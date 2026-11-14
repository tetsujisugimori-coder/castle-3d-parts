"""Hash raw evidence; the enclosing ZIP digest is checked after GitHub download."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=True)
rows = {p.relative_to(root).as_posix(): {'size': p.stat().st_size,
        'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(root.rglob('*')) if p.is_file() and p != root/'sha256.json'}
(root/'sha256.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
