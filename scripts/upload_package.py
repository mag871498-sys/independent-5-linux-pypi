"""Upload the built distributions through Twine to the local devpi index."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
environment = os.environ.copy()
environment['TWINE_USERNAME'] = 'student'
environment['TWINE_PASSWORD'] = Path('/var/lib/study5-devpi-auth/password').read_text().strip()
environment['TWINE_NON_INTERACTIVE'] = '1'
environment['NO_COLOR'] = '1'
files = sorted(str(path.relative_to(ROOT)) for path in (ROOT/'dist').glob('*'))
if not files:
    raise SystemExit('Build distributions before uploading.')
result = subprocess.run([
    sys.executable,'-m','twine','upload','--non-interactive','--disable-progress-bar',
    '--repository-url','http://127.0.0.1:3141/student/lab/',*files,
],cwd=ROOT,env=environment)
raise SystemExit(result.returncode)
