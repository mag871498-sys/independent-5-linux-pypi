"""Capture only the project's own macOS Terminal window; crop title/blank margins."""
import argparse
import ctypes
import getpass
import json
import os
import re
from pathlib import Path
import subprocess
import time

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / 'reports/evidence'
RAW = ROOT / 'reports/tmp/terminal-originals'
RAW.mkdir(parents=True, exist_ok=True)

SCENES = [('journal', 16, ['bash scripts/linux.sh ps -p 1 -o comm=', 'bash scripts/linux.sh journalctl -n 10 --no-pager -o short-iso', 'wc -l logs.txt']), ('ssh', 20, ['bash scripts/linux.sh journalctl -u ssh.service --no-pager', 'wc -l sshd-logs.txt']), ('iostat', 16, ['cat reports/evidence/iostat.txt', 'cat reports/evidence/io-summary.txt']), ('disks', 18, ['cat reports/evidence/disks.txt', 'cat reports/evidence/fdisk.txt']), ('unit-code', 20, ['cat linux/mytest.service linux/heartbeat.sh']), ('service-run', 16, ['bash scripts/linux.sh systemctl status mytest.service --no-pager -n 2', 'bash scripts/linux.sh journalctl -u mytest.service -n 2 --no-pager', 'bash scripts/linux.sh tail -n 2 /tmp/test.log']), ('package-code', 20, ['cat pyproject.toml src/study5_hello/__init__.py']), ('build', 20, ['cat scripts/build_package.sh', 'python3 scripts/show_evidence.py reports/evidence/build.txt --tail 3', 'ls dist/']), ('upload', 20, ['bash scripts/linux.sh systemctl is-active devpi.service', 'cat reports/evidence/upload.txt']), ('install', 20, ['cat reports/evidence/install.txt', 'bash scripts/linux.sh /opt/study5-verify/bin/python -I -m study5_hello']), ('changelog', 22, ['cat CHANGELOG.md']), ('load-code', 20, ['cat loadtest.py scripts/load_test.sh']), ('load-run', 20, ['python3 scripts/show_evidence.py reports/evidence/molotov.txt --tail 6', "bash scripts/linux.sh curl -s -i -w '\\n' http://127.0.0.1:8085/"]), ('github', 18, ['git remote -v', 'git log --oneline -12', 'git branch --show-current'])]


def literal(value):
    return '"' + value.replace('\\','\\\\').replace('"','\\"') + '"'


def apple(script):
    return subprocess.check_output(['osascript','-'],input=script,text=True).strip()


def capture(window_id, selected=None):
    cg=ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    cg.CGPreflightScreenCaptureAccess.restype=ctypes.c_bool
    if not cg.CGPreflightScreenCaptureAccess():
        raise RuntimeError('macOS screen capture permission is required.')
    tab=f'selected tab of window id {window_id}'
    def command(value):
        apple(f'tell application "Terminal" to do script {literal(value)} in {tab}')
        time.sleep(0.35)
        for _ in range(100):
            content=apple(f'tell application "Terminal" to get history of {tab}')
            if content.rstrip().endswith('$'):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError('Command has not completed: '+value)
    # Setup is cleared before capturing; no filesystem/user path appears in evidence.
    import shlex
    command('export PATH='+shlex.quote(str(ROOT/'.venv/bin')+os.pathsep+os.environ['PATH'])+'; export PAGER=cat GIT_PAGER=cat NO_COLOR=1; unset PROMPT_COMMAND; PS1=\'$ \'; cd -- '+shlex.quote(str(ROOT))+'; clear')
    manifest=EVIDENCE/'capture-manifest.json'
    previous=json.loads(manifest.read_text()) if manifest.exists() else []
    metadata={item['name']:item for item in previous}
    for name,font,commands in SCENES:
        if selected and name not in selected:
            continue
        apple(f'''tell application "Terminal"
activate
set font size of current settings of {tab} to {font}
set bounds of window id {window_id} to {{80, 30, 1330, 831}}
end tell''')
        time.sleep(0.4)
        command("printf '\\033[3J\\033[H\\033[2J'")
        for value in commands:
            command(value)
        time.sleep(0.5)
        original=RAW/f'{name}.png'
        for attempt in range(4):
            apple(f'''tell application "Terminal"
activate
set bounds of window id {window_id} to {{80, 30, 1330, 831}}
end tell''')
            time.sleep(1.0)
            capture_result=subprocess.run(['screencapture','-x','-o','-l',str(window_id),str(original)],capture_output=True)
            if capture_result.returncode:
                continue
            with Image.open(original) as check:
                scale=2 if check.width >= 1800 else 1
                sample=check.convert('L').crop((10*scale,40*scale,check.width-20*scale,check.height-20*scale)).resize((100,100))
                white_fraction=sum(sample.histogram()[248:])/10000
                if check.width >= 1100 and check.height >= 720 and white_fraction>0.7:
                    break
        else:
            raise RuntimeError('Window is still moving or hidden: '+name)
        contents=apple(f'tell application "Terminal" to get contents of {tab}')
        for forbidden in ('/Users/',getpass.getuser(),'dckr_pat_','ghp_','github_pat_'):
            if forbidden in contents:
                raise RuntimeError('Private value in terminal content for '+name)
        if 'fatal:' in contents or ('Traceback (most recent call last)' in contents and name not in {'build', 'upload', 'install', 'load-run'}):
            raise RuntimeError('Command failed in '+name)
        (EVIDENCE/f'{name}.terminal.txt').write_text(contents+'\n')
        with Image.open(original) as image:
            # Account for Retina scaling and window animation before removing chrome.
            bounds=[int(n) for n in re.findall(r'-?\d+', apple(f'tell application "Terminal" to get bounds of window id {window_id}'))]
            scale=image.width/(bounds[2]-bounds[0])
            body=image.convert('RGB').crop((round(2*scale),round(28*scale),image.width-round(12*scale),image.height-round(10*scale)))
            mask=body.convert('L').point(lambda p: 255 if p<150 else 0)
            bbox=mask.getbbox()
            if not bbox:
                raise RuntimeError('Empty terminal screenshot: '+name)
            x0,y0,x1,y1=bbox
            body=body.crop((max(0,x0-12),max(0,y0-12),min(body.width,x1+16),min(body.height,y1+14)))
            body.save(EVIDENCE/f'{name}.png')
            metadata[name]={'name':name,'source':'macOS Terminal screenshot','commands':commands,'size':list(body.size),'title_bar_removed':True}
        print('Captured '+name,flush=True)
        manifest.write_text(json.dumps([metadata[n] for n,_,_ in SCENES if n in metadata],ensure_ascii=False,indent=2))
    manifest.write_text(json.dumps([metadata[name] for name,_,_ in SCENES if name in metadata],ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--window-id',type=int,required=True)
    parser.add_argument('--only',nargs='+')
    args=parser.parse_args()
    capture(args.window_id, set(args.only) if args.only else None)
