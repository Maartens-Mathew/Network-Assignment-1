"""Run all probes sequentially with delays between them."""
import subprocess
import sys
import time
from pathlib import Path

probes_dir = Path(__file__).parent / 'probes'
probes = sorted(probes_dir.glob('*.py'))

results = {}
for probe in probes:
    print(f"\n{'#'*60}")
    print(f"# Running: {probe.name}")
    print(f"{'#'*60}")

    try:
        result = subprocess.run(
            [sys.executable, str(probe)],
            capture_output=False,
            timeout=60
        )
        results[probe.name] = result.returncode
    except subprocess.TimeoutExpired:
        results[probe.name] = -1
        print(f"TIMEOUT after 60s")

    time.sleep(2)  # pause between probes to stay under rate limit

print(f"\n{'='*60}")
print("PROBE SUMMARY")
print('='*60)
for name, code in results.items():
    status = 'OK' if code == 0 else 'FAILED/TIMEOUT'
    print(f"  [{status}] {name}")
