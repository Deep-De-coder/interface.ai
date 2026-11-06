"""Verify an isolated, allowlisted source archive without the private kit."""
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/package_submission.py")], check=True)
with tempfile.TemporaryDirectory(prefix="knowledge-release-") as folder:
    with zipfile.ZipFile(ROOT / "dist/submission.zip") as archive:
        for name in archive.namelist():
            if not name.startswith("submission/") or ".." in Path(name).parts:
                raise RuntimeError("Unsafe package entry")
        archive.extractall(folder)
    code = "import sys; sys.path.insert(0,'submission'); from solution import build; s=build(); assert not s.answer('Unknown question').confident; assert s.conflicts()==[]; print('Isolated release import passed')"
    subprocess.run([sys.executable, "-c", code], cwd=folder, check=True)
