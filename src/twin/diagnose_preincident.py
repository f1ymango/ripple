"""Bounded, source-hashed pre-incident replay; never selects a closure lane."""
import argparse
import json
import subprocess
import sys
import time
import re
from collections import Counter
import xml.etree.ElementTree as ET

from src.twin.common import load_json, require_command, resolve
from src.twin.network_sources import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--observations', required=True)
    parser.add_argument('--work', required=True, help='New directory; refuses to overwrite a run')
    parser.add_argument('--out', required=True)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--trace-flow', action='store_true',
                        help='Record per-vehicle departure/arrival and edge traffic for delivery audits')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    cfg = load_json(resolve(args.config))
    end = float(cfg['incident']['start'])
    if end <= float(cfg.get('begin', 0)):
        raise ValueError('No pre-incident interval')
    routes = resolve(cfg['routes'])
    flows = ET.parse(routes).getroot().findall('flow')
    begins = [float(flow.get('begin')) for flow in flows]
    if begins != sorted(begins):
        raise ValueError('Flow departure times are not sorted; regenerate demand')
    work = resolve(args.work)
    work.mkdir(parents=True, exist_ok=False)
    loops = ET.parse(resolve(cfg['detector_additional']))
    for loop in loops.getroot().findall('inductionLoop'):
        loop.set('file', str(work / ('e1_' + loop.get('id') + '.xml')))
    additional = work / 'detectors.add.xml'
    loops.write(additional, encoding='utf-8', xml_declaration=True)
    command = [require_command('sumo'), '-n', str(resolve(cfg['network'])),
               '-r', str(routes), '-a', str(additional), '--begin', str(cfg.get('begin', 0)),
               '--end', str(end), '--seed', str(cfg.get('seed', 2026)),
               '--step-length', str(cfg.get('step_length', 1)),
               '--max-depart-delay', '-1', '--duration-log.statistics', 'true',
               '--statistic-output', str(work / 'statistics.xml'), '--no-step-log', 'true']
    if args.trace_flow:
        command += ['--tripinfo-output', str(work / 'tripinfo.xml'),
                    '--tripinfo-output.write-unfinished', 'true',
                    '--tripinfo-output.write-undeparted', 'true',
                    '--edgedata-output', str(work / 'edge-data.xml')]
    started = time.monotonic()
    timed_out = False
    with (work / 'sumo.log').open('w', encoding='utf-8') as log:
        try:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=args.timeout, check=False)
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            timed_out, returncode = True, None
    report = {'purpose': 'Pre-incident diagnostic only; not full incident P0 validation',
              'command': command, 'timeout_seconds': args.timeout, 'timed_out': timed_out,
              'returncode': returncode, 'wall_seconds': time.monotonic() - started,
              'simulation_end': end, 'seed': cfg.get('seed', 2026), 'sources': {}}
    if args.trace_flow:
        report['flow_trace_files'] = {name: str(work / name)
                                      for name in ('tripinfo.xml', 'edge-data.xml')}
    for label, path in {'config': args.config, 'observations': args.observations,
                        'network': cfg['network'], 'routes': cfg['routes'],
                        'loops': cfg['detector_additional']}.items():
        report['sources'][label] = {'path': str(path), 'sha256': sha256(resolve(path))}
    log_text = (work / 'sumo.log').read_text(encoding='utf-8')
    report['route_loading_warnings'] = [line for line in log_text.splitlines()
                                       if 'sorted by departure' in line or 'Error:' in line]
    report['teleport_start_lanes'] = dict(Counter(re.findall(
        r"Teleporting vehicle .*?lane='([^']+)'", log_text)).most_common())
    report['run_usable'] = returncode == 0 and not timed_out and not report['route_loading_warnings']
    if report['run_usable']:
        report['statistics'] = {child.tag: child.attrib for child in
                                ET.parse(work / 'statistics.xml').getroot()}
        observed = load_json(resolve(args.observations))
        # The export is a complete ordered five-minute grid, including null bins.
        slots = int((end - float(cfg.get('observation_start_sim_seconds',
                                         cfg.get('warmup_seconds', 0)))) / observed['interval_seconds'])
        for detector in observed['detectors']:
            detector['observations'] = detector['observations'][:slots]
        window = work / 'observations.json'
        window.write_text(json.dumps(observed), encoding='utf-8')
        evaluation = work / 'evaluation.json'
        subprocess.run([sys.executable, '-m', 'src.twin.evaluate', '--config', args.config,
                        '--observations', str(window), '--sim', str(work), '--out', str(evaluation)],
                       check=True, timeout=60, stdout=subprocess.DEVNULL)
        report['evaluation'] = load_json(evaluation)
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Diagnostic written: {out}')


if __name__ == '__main__':
    main()
