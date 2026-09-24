import os
import sys
from pathlib import Path

from common import require_command, sumo_tools


try:
    print("SUMO_HOME:", os.environ.get("SUMO_HOME", "(unset)"))
    for name in ("sumo", "netconvert"):
        print(name + ":", require_command(name))
    print("SUMO tools:", sumo_tools())
    try:
        import traci, sumolib
        print("Python TraCI and sumolib: available")
    except ImportError as exc:
        print("Python SUMO modules missing:", exc)
        print("Run: py -m pip install -r requirements.txt")
        raise SystemExit(1)
except RuntimeError as exc:
    print(exc, file=sys.stderr)
    raise SystemExit(1)
