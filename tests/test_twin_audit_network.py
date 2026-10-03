"""The locality audit covers every directed detector chain."""
from src.loaders.corridor import (
    CHAIN_EASTBOUND, CHAIN_WESTBOUND,
    CHAIN_WESTERN_EASTBOUND, CHAIN_WESTERN_WESTBOUND,
)
from src.twin.audit_network import chain_paths


def test_chain_paths_includes_both_main_and_western_legs():
    chains = (
        ("main_eastbound", CHAIN_EASTBOUND),
        ("main_westbound", CHAIN_WESTBOUND),
        ("western_eastbound", CHAIN_WESTERN_EASTBOUND),
        ("western_westbound", CHAIN_WESTERN_WESTBOUND),
    )
    detector_ids = {detector_id for _, chain in chains for detector_id in chain}
    mapping = {detector_id: {"edge_id": detector_id, "position_m": "1"}
               for detector_id in detector_ids}
    registry = {detector_id: {"easting": str(index * 10), "northing": "0"}
                for index, detector_id in enumerate(sorted(detector_ids))}

    class Edge:
        def __init__(self, edge_id):
            self.edge_id = edge_id

        def getID(self):
            return self.edge_id

    class Net:
        def getEdge(self, edge_id):
            return Edge(edge_id)

        def getShortestPath(self, source, destination, **_):
            return [source, destination], 10.0

    result = chain_paths(Net(), mapping, registry)

    assert len(result) == 24
    assert {row["leg"] for row in result} == {leg for leg, _ in chains}
    assert all(row["status"] == "reachable" for row in result)
    assert sum(row["leg"].startswith("western_") for row in result) == 6
