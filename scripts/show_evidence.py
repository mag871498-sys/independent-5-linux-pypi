"""Display actual captured command output, removing only terminal colour codes."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('path', type=Path)
parser.add_argument('--tail', type=int)
args = parser.parse_args()
text = args.path.read_text()
text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
if args.tail:
    text = '\n'.join(text.splitlines()[-args.tail:])
print(text.rstrip())
