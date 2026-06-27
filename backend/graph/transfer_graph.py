"""
transfer_graph.py — merges the metro and bus graphs, then adds
walk-transfer edges between nearby stops of different modes.

Transfer edge attributes:
    weight      float   walking time in minutes
    mode        str     "walk"
    from_stop   str     origin stop name
    to_stop     str     destination stop name
"""

import networkx as nx
from haversine import haversine, Unit


WALK_SPEED_KMH    = 4.5   # average walking speed
MAX_TRANSFER_M    = 200   # only link stops within this distance
TRANSFER_PENALTY  = 5.0   # extra minutes added per mode change


def _walk_time(lat1, lon1, lat2, lon2) -> float:
    """Walking time in minutes between two coordinates."""
    dist_km = haversine((lat1, lon1), (lat2, lon2), unit=Unit.KILOMETERS)
    return (dist_km / WALK_SPEED_KMH) * 60 + TRANSFER_PENALTY


def build_combined_graph(metro_G: nx.DiGraph,
                         bus_G: nx.DiGraph) -> nx.DiGraph:
    """
    Merge metro and bus graphs, then add transfer walk edges.

    Args:
        metro_G : graph from build_metro_graph()
        bus_G   : graph from build_bus_graph()

    Returns:
        Combined nx.DiGraph
    """
    G = nx.DiGraph()

    # Copy all nodes and edges from both graphs
    G.add_nodes_from(metro_G.nodes(data=True))
    G.add_edges_from(metro_G.edges(data=True))
    G.add_nodes_from(bus_G.nodes(data=True))
    G.add_edges_from(bus_G.edges(data=True))

    print(f"[transfer] Combined: {G.number_of_nodes():,} nodes, "
          f"{G.number_of_edges():,} edges before transfers")

    # ── Find nearby cross-mode stop pairs ────────────────────────────────────
    metro_nodes = [(n, d) for n, d in G.nodes(data=True)
                   if d.get("mode") == "metro"]
    bus_nodes   = [(n, d) for n, d in G.nodes(data=True)
                   if d.get("mode") == "bus"]

    transfers_added = 0

    for metro_id, metro_data in metro_nodes:
        for bus_id, bus_data in bus_nodes:
            dist_m = haversine(
                (metro_data["lat"], metro_data["lon"]),
                (bus_data["lat"],   bus_data["lon"]),
                unit=Unit.METERS
            )

            if dist_m <= MAX_TRANSFER_M:
                walk_t = _walk_time(
                    metro_data["lat"], metro_data["lon"],
                    bus_data["lat"],   bus_data["lon"]
                )

                # Transfer is bidirectional
                G.add_edge(metro_id, bus_id,
                           weight=walk_t,
                           mode="walk",
                           from_stop=metro_data["name"],
                           to_stop=bus_data["name"])
                G.add_edge(bus_id, metro_id,
                           weight=walk_t,
                           mode="walk",
                           from_stop=bus_data["name"],
                           to_stop=metro_data["name"])
                transfers_added += 2

    print(f"[transfer] {transfers_added} transfer edges added "
          f"(within {MAX_TRANSFER_M}m, +{TRANSFER_PENALTY} min penalty)")
    print(f"[transfer] Final graph: {G.number_of_nodes():,} nodes, "
          f"{G.number_of_edges():,} edges")

    return G
