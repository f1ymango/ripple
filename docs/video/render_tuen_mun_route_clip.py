"""Build a nine-second map insert from the frozen P2 network path frames."""

from pathlib import Path
import os
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
OUT = HERE / "tuen-mun-route-2026-10-18.mp4"

with tempfile.TemporaryDirectory() as temp:
    frames = Path(temp) / "frames.txt"
    lines = []
    for i in (0, 2, 4, 6, 8):
        image = HERE / "tuen-mun-route-frames" / f"route-{i:02d}.png"
        lines.extend((f"file '{image}'", "duration 0.9"))
    lines.extend((f"file '{HERE / 'tuen-mun-route-frames' / 'route-09.png'}'", "duration 4.5"))
    lines.append(f"file '{HERE / 'tuen-mun-route-frames' / 'route-09.png'}'")
    frames.write_text("\n".join(lines) + "\n")
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(frames), "-vf", "fps=24", "-t", "9", "-c:v", "libx264",
        "-crf", "18", "-pix_fmt", "yuv420p", str(OUT),
    ], check=True)
print(OUT)
