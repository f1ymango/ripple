# Full traffic-only recording — 30 September

[Play MP4](../results/twin/aberdeen-full-traffic-sept30.mp4)

Actual SUMO FCD vehicle positions, sampled every 30 simulation seconds and
played at 4 frames per second (120x time compression). Duration: 87.5 seconds,
350 frames, 1200 x 760 pixels. The simulation completed 0–10,500 seconds;
sampled frames cover 0–10,470 seconds. No vehicle positions are interpolated.
Green means speed above 3 m/s; amber means 3 m/s or below. Red marks the
flyover location, not an active closure. This is an overview rendering of
recorded simulation output, not a screen recording of SUMO GUI.

The user selected no assumed closure. The run uses the original full-horizon
fitted demand without incident-origin suspension. There is no incident or
response plan simulated. The network is provisional and unvalidated.

The [run manifest](../results/twin/full-video-sept30-run.json) contains the
command, seed, network/route hashes, wall-time limit and SUMO statistics.
It completed in 157.52 wall seconds within a 420-second limit: 41,756 vehicles
loaded, 32,481 inserted, 9,275 waiting to enter at the horizon, 428 teleports.
These limitations prevent presenting the recording as validated traffic reality.

Encoding requires `imageio-ffmpeg==0.6.0` from requirements.txt:

```powershell
python -m src.twin.render_fcd --fcd sim/work/full-video-sept30/traffic.fcd.xml --network sim/work/aberdeen.net.xml --out results/twin/aberdeen-full-traffic-sept30.mp4 --incident-edge 44419212 --every-seconds 30 --traffic-only
```

The MP4 was fully decoded without errors and a frame was visually inspected.
The raw FCD and provisional network remain in ignored local sim/work storage.
