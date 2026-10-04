"""Package only explicit, source-checked diagnostic inputs for team reproduction."""
import argparse
import json
import zipfile

from src.twin.common import ROOT, load_json, resolve
from src.twin.network_sources import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostic', required=True)
    parser.add_argument('--osm', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--extra', nargs='*', default=[],
                        help='Explicit in-repository evidence/build files needed to regenerate demand')
    args = parser.parse_args()
    run = load_json(resolve(args.diagnostic))
    files = {}
    for entry in run['sources'].values():
        path = resolve(entry['path'])
        if sha256(path) != entry['sha256']:
            raise ValueError(f'Source changed since run: {path}')
        files[path] = entry['sha256']
    cfg = load_json(resolve(run['sources']['config']['path']))
    for path in (resolve(cfg['candidate_routes']),
                 resolve(cfg['detector_additional']).with_suffix('.csv'),
                 resolve(args.osm), resolve(args.diagnostic)):
        files[path] = sha256(path)
    for extra in args.extra:
        path = resolve(extra)
        files[path] = sha256(path)
    members = {}
    for path, digest in files.items():
        # Never archive arbitrary external paths or recursively scan directories.
        name = path.relative_to(ROOT).as_posix()
        members[name] = {'sha256': digest, 'bytes': path.stat().st_size}
    manifest = {'status': 'PROVISIONAL DIAGNOSTIC INPUTS; NOT A REVIEWED NETWORK RELEASE',
                'purpose': 'Reproduce the recorded no-closure calibration on Windows in an isolated repository checkout',
                'diagnostic': args.diagnostic, 'files': members,
                'limitations': ['OSM and detector placement remain provisional.',
                                'Detector export is included; raw TD archive snapshots are not.',
                                'Use a fresh checkout so extraction does not replace local work.']}
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr('diagnostic-input-manifest.json', json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(out) as archive:
        if archive.testzip() is not None:
            raise ValueError('Archive integrity check failed')
    manifest['archive_sha256'] = sha256(out)
    manifest['archive_bytes'] = out.stat().st_size
    out.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Packed {len(files)} checked files: {out}')


if __name__ == '__main__':
    main()
