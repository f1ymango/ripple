# Simulation paragraph for Impact — due Friday 2 October

Component C now runs a reproducible SUMO model of the Aberdeen corridor using
OpenStreetMap and Transport Department observations. We corrected left-hand
conversion, detector aggregation across lanes, observation timestamp matching,
pre-incident demand fitting and route departure ordering, and added source
audits and bounded replay tooling. The latest no-closure calibration replay
completed the May 15 07:55–08:55 observation window after a 15-minute warm-up:
66.94% of 242 count bins achieved GEH < 5, below the 85% target, while speed MAPE
was 36.84% across 296 bins, above the approximately 15% target. It recorded 123
teleports and 2,378 vehicles waiting to enter, so the baseline remains
unvalidated. We identified the model flyover edge towards Aberdeen Tunnel and
its Slow/Fast lane mapping, but physical placement reviews and Data/E's initial
closure assumption and phase timing remain open. A separate full-horizon,
traffic-only diagnostic MP4 is available; it demonstrates execution, not
validated incident reproduction. We are prioritising tunnel-approach and demand
diagnosis while Data develops the simplified-network fallback for 4 October.

Evidence links on the simulation branch (latest changes are awaiting merge):

- [Calibration report](../results/twin/sept30-preincident-diagnosis.json)
- [Diagnosis and limitations](component-c-diagnosis-2026-09-30.md)
- [Full traffic-only video](../results/twin/aberdeen-full-traffic-sept30.mp4)
- [Video manifest](../results/twin/full-video-sept30-run.json)
- [Data/E handoff and next run plan](simulation-handoff-2026-10-01.md)

Prepared 1 October for Impact's Friday collection, Saturday assembly and
Sunday 4 October go/no-go. Repository publication does not confirm delivery
through a team messaging channel.
