"""Bounded I/O sample on the Docker VM disk; keep the actual iostat output."""
from pathlib import Path
import subprocess
import tempfile
import threading
import time

path = Path(tempfile.mkstemp(prefix="study5-io-", dir="/var/tmp")[1])


def write_sample():
    for _ in range(4):
        time.sleep(0.35)
        subprocess.run([
            "dd", "if=/dev/zero", f"of={path}", "bs=1M", "count=16",
            "conv=fdatasync", "status=none",
        ], check=True)


worker = threading.Thread(target=write_sample)
try:
    worker.start()
    result = subprocess.run(["iostat", "-d", "-y", "vda", "1", "2"], capture_output=True, text=True, check=True)
    worker.join()
    Path("reports/evidence/iostat.txt").write_text(result.stdout)
    print(result.stdout, end="")
    sample = [line.split() for line in result.stdout.splitlines() if line.startswith("vda ")][-1]
    summary = f"vda: tps (observed IOPS) = {sample[1]}; read kB/s = {sample[2]}; write kB/s = {sample[3]}\n"
    Path("reports/evidence/io-summary.txt").write_text(summary)
    print(summary, end="")
finally:
    worker.join()
    path.unlink(missing_ok=True)
