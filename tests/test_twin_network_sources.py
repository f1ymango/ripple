import gzip
import json
from pathlib import Path

import pytest

from src.twin.network_sources import (
    apply_mapping_overrides, cached_lane_evidence, edge_names, read_osm_ways, sha256,
    verify_lane_evidence,
)
from src.twin.place_detectors import _candidate_name_score, _choose_named_candidate


class MockLane:
    def __init__(self, width):
        self.width = width

    def getWidth(self):
        return self.width


class MockEdge:
    def __init__(self, edge_id, lane_count, name=''):
        self.edge_id, self.lane_count, self.name = edge_id, lane_count, name

    def getID(self):
        return self.edge_id

    def getName(self):
        return self.name

    def getLaneNumber(self):
        return self.lane_count

    def getLanes(self):
        return [MockLane(3.3) for _ in range(self.lane_count)]


def test_osm_alternate_street_name_is_kept_and_requires_lane_evidence():
    ways = read_osm_ways(Path('tests/fixtures/mock_osm_aliases.xml'))
    edge = MockEdge('mock_901#0', 2, 'Aberdeen Tunnel')
    assert edge_names(edge, ways) == ['Aberdeen Tunnel', 'Wong Chuk Hang Road']
    assert _candidate_name_score('Wong Chuk Hang Road', edge, ways, None) == 0
    assert _candidate_name_score('Wong Chuk Hang Road', edge, ways, 2) == 2
    assert _candidate_name_score('Wong Chuk Hang Road', edge, ways, 3) == 0


def test_lane_scope_only_breaks_a_nearby_parallel_edge_tie():
    wrong = (MockEdge('mock_1', 2), 4.0, 0.99, 2)
    matching = (MockEdge('mock_2', 3), 6.0, 0.98, 2)
    far_matching = (MockEdge('mock_3', 3), 12.0, 0.99, 2)
    assert _choose_named_candidate([wrong, matching], 3) == matching
    assert _choose_named_candidate([wrong, far_matching], 3) == wrong
    assert _choose_named_candidate([wrong, matching], None) == wrong


def test_lane_evidence_uses_period_timestamps_inside_cached_snapshot(tmp_path):
    cache = tmp_path / 'detectors'
    cache.mkdir()
    source = Path('tests/fixtures/detector_snapshot_20260921-0830.xml')
    with gzip.open(cache / '20260921-0830.xml.gz', 'wb') as destination:
        destination.write(source.read_bytes())
    # The archive label is 08:30; the reading inside it is 08:21.
    evidence = cached_lane_evidence(
        cache, ['2026-09-21T08:20:00+08:00', '2026-09-21T08:22:00+08:00'], ['AID01101'])
    assert evidence['detectors']['AID01101']['lane_count'] == 3
    assert evidence['detectors']['AID01101']['observed_periods'] == 2
    outside = cached_lane_evidence(
        cache, ['2026-09-21T08:30:00+08:00', '2026-09-21T08:31:00+08:00'], ['AID01101'])
    assert outside['detectors']['AID01101']['lane_count'] is None


def test_overrides_are_pinned_to_network_and_registry_hashes(tmp_path):
    network, registry, override_path = (tmp_path / name for name in ('mock.net', 'mock.csv', 'overrides.json'))
    network.write_text('network a', encoding='utf-8')
    registry.write_text('registry a', encoding='utf-8')
    override_path.write_text(json.dumps({
        'network_sha256': sha256(network), 'registry_sha256': sha256(registry),
        'window': ['start', 'end'],
        'detectors': {'mock-det': {'edge_id': 'mock_7', 'position_m': 12.5,
                                  'evidence': {'td_lanes': ['Fast Lane', 'Slow Lane']}}},
    }), encoding='utf-8')
    data = {'source': {'window': ['start', 'end']},
            'detectors': [{'id': 'mock-det', 'edge_id': None, 'position_m': None}]}
    lane_evidence = {'mock-det': {'lane_count': 2, 'lane_sets': [['Fast Lane', 'Slow Lane']]}}
    pinned = apply_mapping_overrides(data, override_path, network, registry, lane_evidence)
    assert pinned['detectors'][0]['edge_id'] == 'mock_7'
    with pytest.raises(ValueError, match='lane evidence differs'):
        apply_mapping_overrides(data, override_path, network, registry,
                                {'mock-det': {'lane_count': 2, 'lane_sets': [['Fast Lane', 'Middle Lane']]}})
    network.write_text('network b', encoding='utf-8')
    with pytest.raises(ValueError, match='network hash differs'):
        apply_mapping_overrides(data, override_path, network, registry, lane_evidence)


def test_lane_evidence_rejects_different_handover_or_cache_snapshot(tmp_path):
    registry, handover, snapshot = (tmp_path / name for name in ('registry.csv', 'detectors.json', 'raw.xml.gz'))
    for path, value in ((registry, 'registry'), (handover, 'observations'), (snapshot, 'snapshot')):
        path.write_text(value, encoding='utf-8')
    evidence = {
        'sources': {'registry': {'sha256': sha256(registry)},
                    'observations': {'sha256': sha256(handover)}},
        'lane_evidence': {'window': ['start', 'end'],
                          'sources': [{'path': str(snapshot), 'sha256': sha256(snapshot)}],
                          'detectors': {'mock-det': {'lane_count': 2}}},
    }
    assert verify_lane_evidence(evidence, ['start', 'end'], handover, registry)['mock-det']['lane_count'] == 2
    handover.write_text('new observations', encoding='utf-8')
    with pytest.raises(ValueError, match='observations hash differs'):
        verify_lane_evidence(evidence, ['start', 'end'], handover, registry)
    handover.write_text('observations', encoding='utf-8')
    snapshot.write_text('new snapshot', encoding='utf-8')
    with pytest.raises(ValueError, match='snapshot used by lane evidence'):
        verify_lane_evidence(evidence, ['start', 'end'], handover, registry)
