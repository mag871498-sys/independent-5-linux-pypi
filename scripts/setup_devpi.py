"""Configure a local devpi index without printing its generated password."""
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import urllib.request

BIN = Path('/opt/lab-venv/bin')
BASE = 'http://127.0.0.1:3141'
state = Path('/var/lib/study5-devpi-auth')
state.mkdir(mode=0o700, exist_ok=True)
password_file = state/'password'
if not password_file.exists():
    password_file.write_text(secrets.token_urlsafe(24))
    password_file.chmod(0o600)
password = password_file.read_text().strip()


def run(arguments):
    result = subprocess.run(arguments, capture_output=True, text=True)
    if result.returncode:
        safe = (result.stdout + result.stderr).replace(password, '<secret>')
        raise RuntimeError(safe)


def exists(url):
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            return response.status == 200
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise


if not Path('/var/lib/study5-devpi/.nodeinfo').exists():
    run([str(BIN/'devpi-init'), '--serverdir', '/var/lib/study5-devpi',
         '--no-root-pypi', '--root-passwd', password])
run(['install','-m','644','/work/linux/devpi.service','/etc/systemd/system/devpi.service'])
run(['systemctl','daemon-reload'])
run(['systemctl','enable','--now','devpi.service'])
for _ in range(100):
    try:
        if exists(BASE+'/+status'):
            break
    except OSError:
        pass
    time.sleep(0.1)
else:
    raise RuntimeError('devpi did not become ready')
client = str(BIN/'devpi')
run([client,'use',BASE])
run([client,'login','root','--password',password])
if not exists(BASE+'/student'):
    run([client,'user','-c','student','password='+password])
run([client,'login','student','--password',password])
if not exists(BASE+'/student/lab'):
    run([client,'index','-c','lab','bases='])
run([client,'use','student/lab'])
print('devpi ready: '+BASE+'/student/lab/')
print('Public installation index: '+BASE+'/student/lab/+simple/')
print('Credentials kept outside /work; no password in source or report.')
