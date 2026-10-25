"""Verify packaged files without making any changes."""
from pathlib import Path
import hashlib
import json
import sys
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'BUNDLE_MANIFEST.json').read_text())
failures=[]
for name,expected in manifest['sha256'].items():
 path=root/name
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
  failures.append(name)
if failures:
 print('Missing or changed files:',*failures,sep='\n');sys.exit(1)
print(f"Verified {len(manifest['sha256'])} bundled files. Extra files such as .venv are not checked.")
