# TD lane-scope cross-check

Source: DATA.GOV.HK historical archive, TD raw detector feed.
Cross-check lane labels on a separate day; not incident-window calibration.

Only the listed archive snapshots are used. Timestamps below come from the XML periods, not filenames.

| Detector | Observed periods | Lane counts | Lane sets |
|---|---:|---|---|
| AID01105 | 0 | no observations | no lane labels observed |
| AID01220 | 0 | no observations | no lane labels observed |
| TDSSPWR20002 | 0 | no observations | no lane labels observed |
| AID01221 | 12 | 3 | Fast Lane / Middle Lane / Slow Lane |
| AID01222 | 12 | 3 | Fast Lane / Middle Lane / Slow Lane |
| TDSAPR10001 | 8 | 3 | Fast Lane / Middle Lane / Slow Lane |

## Source snapshots

| Archive timestamp | Status | SHA-256 |
|---|---|---|
| 20260514-0731 | read | 99c55fba6be85703088c2c2cc5e5e385c9f52ed4f7e3088bf761a445324bca81 |
| 20260514-0802 | read | dcb6a6cecbf7860c4c2c79e6017a8727ef93522ef3666d3bb06465b0c4b1da83 |
| 20260514-0830 | read | 959221861652a42bdbf0a12d071753402694aff7a49c5d58386871b4119df08d |
| 20260514-0900 | archive_404 | — |
| 20260514-0930 | read | 81d660db51088a60708f7ac409f57233b5b801d8a4a8e303cd5fb7e4eb2e20e9 |
| 20260514-1002 | read | 60bcc708be4250c61316bd9f338828ea05b71503fe21e086adc0fff659266d5a |
| 20260514-1030 | read | 5c4fc777af62e584aa5884497af734fa8b6b694ab99bd7fc58c4f722a33ed8d6 |

## Limits

- This sample does not fill missing May 15 incident-window observations.
- A repeated feed lane count does not prove that a SUMO edge is mapped to the right physical carriageway.
- No detector mapping, OSM tag, geometry, lane count, or traffic observation is changed.
