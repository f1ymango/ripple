"""Tuen Mun P0 fits: each P0 run scored against TD's detectors on criteria fixed before choosing one.

    python scripts/tuen_mun/score_fits.py [results dir, default sim/work/tuen-mun/fit]

Per run: validation v2; congested (under 30 km/h) 5-minute bins at TDS90020-32, TD vs model and both;
vehicles past TDS90024/29/33 over 17:30-20:30, model minus TD; E's delay; drivers who left at Ting Kau.
TD's readings come from the archive cache through src/loaders/detectors.py, all of them, before any
count is withheld for the validation data.
"""
import sys, glob, json, datetime as dt, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.loaders import detectors
HK = dt.timezone(dt.timedelta(hours=8))
_s, _e = dt.datetime(2026, 4, 15, 16, 0, tzinfo=HK), dt.datetime(2026, 4, 15, 20, 30, tzinfo=HK)
_ids = [f"TDS900{n}" for n in range(17, 44)]
_rows = detectors.load_window(_s, _e, _ids, log=lambda *a: None)
obs5 = {(b['detector_id'], b['bin_start'][11:16]): b for b in detectors.bin_window(_rows, 5, start=_s, end=_e, detector_ids=_ids)}
obs15 = {(b['detector_id'], b['bin_start'][11:16]): b['flow_veh_h'] for b in detectors.bin_window(_rows, 15, start=_s, end=_e, detector_ids=_ids)}
QD = ['TDS90020', 'TDS90021', 'TDS90022', 'TDS90023', 'TDS90024', 'TDS90025', 'TDS90027', 'TDS90028', 'TDS90029', 'TDS90030', 'TDS90031', 'TDS90032']
def clock(b): t = 16 * 60 + 30 + b // 60; return f"{t // 60:02d}:{t % 60:02d}"
print(f"{'fit':8} {'GEH':>6} {'FFerr':>6} {'state':>6} {'wrongTP':>7} | {'queue bins obs/model/both':>26} | {'counts 24 29 33 (model-obs)':>28} | delay veh-h  left")
RES = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'sim/work/tuen-mun/fit')
for res in sorted(glob.glob(str(RES / 'runs' / '*.json'))):
    if res.endswith('.provenance.json') or '_P0_' not in res:
        continue
    r = json.load(open(res)); run = r['run_id']; label = '_'.join(run.split('_')[3:6])
    v = r['validation']; work = ROOT / 'sim/work/evaluator' / run
    n, sv = defaultdict(float), defaultdict(float)
    for f in glob.glob(f'{work}/results/e1_*.xml'):
        det = f.split('e1_')[1].rsplit('_', 1)[0]
        for iv in ET.parse(f).getroot().iter('interval'):
            b = int(float(iv.get('begin'))); k = float(iv.get('nVehContrib')); s = float(iv.get('speed'))
            n[(det, b)] += k
            if k > 0 and s >= 0: sv[(det, b)] += k * s * 3.6
    ob = mo = both = 0
    for d in QD:
        for b in range(3600, 12000, 300):
            x = obs5.get((d, clock(b)), {}).get('speed_kmh')
            oq = x not in (None, '') and float(x) < 30
            mq = n[(d, b)] > 0 and sv[(d, b)] / n[(d, b)] < 30
            ob += oq; mo += mq; both += oq and mq
    cnt = []
    for d in ['TDS90024', 'TDS90029', 'TDS90033']:
        o_ = sum(float(x) / 4 for (dd, t), x in obs15.items() if dd == d and '17:30' <= t < '20:30' and x not in (None, ''))
        m_ = sum(k for (dd, b), k in n.items() if dd == d and 3600 <= b < 14400)
        cnt.append(round(m_ - o_))
    left = json.load(open(f'{work}/left-corridor.json'))
    print(f"{label:8} {v['geh_under_5_pct']:6.1f} {v['speed_mape_free_flow_pct']:6.1f} {v['congestion_state_agreement_pct']:6.1f} {v['wrong_lane_teleports_other']:7} | {ob:8} {mo:8} {both:8} | {str(cnt):>28} | {r['metrics']['total_vehicle_hours_delay']:8.0f} {len(left):5}")
