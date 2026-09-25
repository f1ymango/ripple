import json
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]  # the repo root: relative paths resolve from here


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def sumo_tools():
    home = os.environ.get("SUMO_HOME")
    if not home:
        raise RuntimeError("SUMO_HOME is not set. Set it to your SUMO installation directory.")
    tools = Path(home) / "tools"
    if not tools.exists():
        raise RuntimeError(f"SUMO tools directory not found: {tools}")
    return tools


def require_command(name):
    command = shutil.which(name)
    if not command:
        raise RuntimeError(f"{name} was not found on PATH. Install SUMO and configure PATH.")
    return command


def run(cmd, cwd=None):
    import subprocess
    print("+", " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), cwd=cwd, check=True)


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)
