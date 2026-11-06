"""Create a source-only submission archive from a strict allowlist."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "dist"
out.mkdir(exist_ok=True)
files = sorted((ROOT / "submission").glob("*.py")) + [ROOT / "submission/requirements.txt", ROOT / "submission/NOTES.md"]
with zipfile.ZipFile(out / "submission.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, "submission/" + path.name)
manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Packaged {len(files)} allowlisted source/documentation files; no website snapshots or derived evidence.")
