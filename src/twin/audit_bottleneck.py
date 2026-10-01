"""Record local lane connections and OSM tags without changing the network."""
import argparse
import json
import xml.etree.ElementTree as ET
from collections import defaultdict

import sumolib
from src.twin.common import resolve, load_json
from src.twin.network_sources import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network', required=True)
    parser.add_argument('--osm', required=True)
    parser.add_argument('--diagnostic', required=True)
    parser.add_argument('--edges', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    ids = args.edges.split(',')
    net = sumolib.net.readNet(str(resolve(args.network)))
    tags = {}
    for _, elem in ET.iterparse(resolve(args.osm), events=('end',)):
        if elem.tag == 'way':
            if elem.get('id') in ids:
                tags[elem.get('id')] = {x.get('k'): x.get('v') for x in elem.findall('tag')}
            elem.clear()
    report = {'purpose': 'Review evidence only; not proof of a topology defect',
              'sources': {key: {'path': value, 'sha256': sha256(resolve(value))}
                          for key, value in {'network': args.network, 'osm': args.osm,
                                             'diagnostic': args.diagnostic}.items()}, 'edges': []}
    for edge_id in ids:
        edge = net.getEdge(edge_id)
        source_tags = tags.get(edge_id, {})
        report['edges'].append({
            'id': edge_id, 'name': edge.getName(), 'length_m': edge.getLength(),
            'osm_tags': source_tags,
            'osm_motor_vehicle_lane_tag_count': len(source_tags['motor_vehicle:lanes'].split('|'))
            if 'motor_vehicle:lanes' in source_tags else None,
            'lanes': [{'id': lane.getID(), 'speed_mps': lane.getSpeed(),
                       'allows_passenger': lane.allows('passenger'),
                       'outgoing_lanes': [c.getToLane().getID() for c in lane.getOutgoing()],
                       'outgoing_passenger_lanes': [c.getToLane().getID() for c in lane.getOutgoing()
                                                    if c.getToLane().allows('passenger')]}
                      for lane in edge.getLanes()]})
    evaluation = load_json(resolve(args.diagnostic))['evaluation']
    rows = defaultdict(list)
    for row in evaluation['count_bins']:
        rows[row['detector_id']].append(row)
    report['detector_counts'] = sorted([
        {'id': key, 'bins': len(items), 'passing_bins': sum(x['within_5'] for x in items),
         'observed_sum': sum(x['observed'] for x in items),
         'simulated_sum': sum(x['simulated'] for x in items)} for key, items in rows.items()],
        key=lambda row: row['passing_bins'] / row['bins'])
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
