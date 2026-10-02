"""Reproduce the recorded experimental tunnel passenger-permission patch."""
import argparse
import xml.etree.ElementTree as ET

from src.twin.common import load_json, resolve
from src.twin.network_sources import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', required=True)
    parser.add_argument('--network', required=True)
    parser.add_argument('--osm', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    review = load_json(resolve(args.review))
    for key in ('network', 'osm'):
        if sha256(resolve(getattr(args, key))) != review['sources'][key]:
            raise ValueError(f'{key} source changed; repeat physical/source review')
    source = ET.parse(resolve(args.osm))
    way = source.find(f"./way[@id='{review['edge']}']")
    tags = {tag.get('k'): tag.get('v') for tag in way.findall('tag')} if way is not None else {}
    if tags != review['osm_tags']:
        raise ValueError('Recorded OSM evidence differs')
    # This intentionally supports only the documented four-lane experiment,
    # not inference of arbitrary conditional or mismatched OSM access tags.
    if (review['edge'] != '1198101424' or review['lane'] != '1198101424_0'
            or tags.get('oneway') != 'yes' or tags.get('lanes') != '4'
            or tags.get('motor_vehicle:lanes') != 'no|yes|yes|yes'):
        raise ValueError('Unsupported permission review')
    tree = ET.parse(resolve(args.network))
    lane = tree.find("./edge[@id='1198101424']/lane[@id='1198101424_0']")
    if lane is None or lane.attrib != review['before'] or 'allow' in lane.attrib:
        raise ValueError('Lane differs from reviewed source')
    lane.set('disallow', ' '.join(sorted(set(lane.get('disallow', '').split()) | {'passenger'})))
    if lane.attrib != review['after']:
        raise ValueError('Review includes changes beyond passenger permission')
    out = resolve(args.out)
    if out.exists():
        raise FileExistsError('Use a new output path; original network must be preserved')
    out.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out, encoding='utf-8', xml_declaration=True)
    if sha256(out) != review['output_sha256']:
        raise ValueError('Output differs from recorded experimental network')
    print(f'Experimental network reproduced: {out}')


if __name__ == '__main__':
    main()
