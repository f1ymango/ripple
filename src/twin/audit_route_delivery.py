"""Attribute insertion queues to route origins and expose indistinguishable fit targets."""
import argparse
import csv
import json
import xml.etree.ElementTree as ET
from collections import defaultdict

import sumolib
from src.twin.common import load_json, resolve
from src.twin.network_sources import sha256
from src.twin.route_crossings import crosses_detector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--diagnostic', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    cfg = load_json(resolve(args.config))
    run = load_json(resolve(args.diagnostic))
    if not run['run_usable'] or 'flow_trace_files' not in run:
        raise ValueError('Need a completed --trace-flow diagnostic')
    for label, key in [('network', 'network'), ('routes', 'routes')]:
        if sha256(resolve(cfg[key])) != run['sources'][label]['sha256']:
            raise ValueError(f'{label} differs from traced run')
    mapping = resolve(cfg['detector_additional']).with_suffix('.csv')
    detectors = {}
    with mapping.open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            detectors[row['detector_id']] = {'edge': row['edge_id'], 'position_m': float(row['position_m'])}
    routes = {}
    for flow in ET.parse(resolve(cfg['routes'])).getroot().findall('flow'):
        path = flow.find('route').get('edges').split()
        routes[flow.get('id')] = {'origin': path[0], 'destination': path[-1], 'edges': path,
                                'inserted': 0, 'undeparted': 0, 'arrived': 0,
                                'unfinished': 0, 'departure_delay_sum_s': 0.0}
    trace = resolve(run['flow_trace_files']['tripinfo.xml'])
    for _, element in ET.iterparse(trace, events=('end',)):
        if element.tag != 'tripinfo':
            continue
        route_id = element.get('id').rsplit('.', 1)[0]
        if route_id not in routes:
            raise ValueError(f'Unknown generated flow: {route_id}')
        row = routes[route_id]
        if float(element.get('depart')) < 0:
            row['undeparted'] += 1
        else:
            row['inserted'] += 1
            row['departure_delay_sum_s'] += float(element.get('departDelay'))
            row['arrived' if float(element.get('arrival')) >= 0 else 'unfinished'] += 1
        element.clear()
    net = sumolib.net.readNet(str(resolve(cfg['network'])))
    origins = {}
    for row in routes.values():
        origin = origins.setdefault(row['origin'], {'inserted': 0, 'undeparted': 0, 'routes': 0})
        origin['routes'] += 1
        for key in ('inserted', 'undeparted'):
            origin[key] += row[key]
    for edge_id, row in origins.items():
        edge = net.getEdge(edge_id)
        row['edge_length_m'] = edge.getLength()
        row['lane_count'] = len(edge.getLanes())
        row['incoming_edges'] = sorted(e.getID() for e in edge.getIncoming())
        row['detectors'] = {key: d['position_m'] for key, d in detectors.items() if d['edge'] == edge_id}
    candidates = ET.parse(resolve(cfg['candidate_routes'])).getroot()
    candidates = [item for item in candidates if item.tag in ('vehicle', 'flow') and item.find('route') is not None]
    lengths = {e.getID(): e.getLength() for e in net.getEdges()}
    signatures = defaultdict(list)
    for detector_id, detector in detectors.items():
        signature = tuple(i for i, item in enumerate(candidates) if crosses_detector(
            item.find('route').get('edges').split(), detector['edge'], detector['position_m'], lengths,
            item.get('departPos', '0'), item.get('arrivalPos', 'max')))
        signatures[signature].append(detector_id)
    totals = {key: sum(row[key] for row in routes.values()) for key in ('inserted', 'undeparted')}
    expected = run['statistics']['vehicles']
    if totals != {'inserted': int(expected['inserted']), 'undeparted': int(expected['waiting'])}:
        raise ValueError(f'Trip trace does not reconcile with SUMO totals: {totals} versus {expected}')
    sources = {'config': resolve(args.config), 'diagnostic': resolve(args.diagnostic),
               'mapping': mapping, 'tripinfo': trace, 'candidates': resolve(cfg['candidate_routes'])}
    report = {'purpose': 'Delivery attribution, not an OD estimate or justification for invented entry roads',
              'sources': {key: {'path': str(path), 'sha256': sha256(path)} for key, path in sources.items()},
              'tripinfo_totals_match_statistics': True, 'totals': totals,
              'origins': dict(sorted(origins.items(), key=lambda pair: -pair[1]['undeparted'])),
              'routes': routes, 'indistinguishable_candidate_crossings': [
                  {'detectors': {key: detectors[key] for key in ids}, 'candidate_indices': list(signature)}
                  for signature, ids in signatures.items() if len(ids) > 1],
              'limitations': ['Geometric crossing eligibility does not prove actual detector passage.',
                             'Detectors on the same edge still have identical signatures for full-edge routes.',
                             'Trip traces include warm-up and the complete simulated horizon, not only scored observation bins.']}
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
