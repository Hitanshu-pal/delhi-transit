"""
bus_graph.py — builds a directed NetworkX graph for DTC buses.

The bus feed is large (3.7M stop_time rows) so we sample one
representative trip per route to keep build time under 30 seconds.

Node ID format : "bus:<stop_id>"
Edge attributes:
    weight      float   travel time in minutes
    mode        str     "bus"
    route_id    str     DTC route number
    from_stop   str     stop name
    to_stop     str     stop name
"""

import pandas as pd
import networkx as nx


HEADWAY_MINUTES = 8.0   # average bus wait time


def _parse_time(t: str) -> float:
    h, m, s = str(t).strip().split(":")
    return int(h) * 60 + int(m) + int(s) / 60


def build_bus_graph(data_dir: str) -> nx.DiGraph:
    """
    Build bus graph from GTFS files in data_dir/dtc/.

    Args:
        data_dir: path to the backend/data folder

    Returns:
        nx.DiGraph with time-cost edges
    """
    import os
    dtc = os.path.join(data_dir, "dtc")

    print("[bus_graph] Loading stops...")
    stops = pd.read_csv(os.path.join(dtc, "stops.txt"))
    stops.columns = stops.columns.str.strip().str.lower()

    print("[bus_graph] Loading trips...")
    trips = pd.read_csv(os.path.join(dtc, "trips.txt"))
    trips.columns = trips.columns.str.strip().str.lower()

    print("[bus_graph] Loading stop_times (large file, may take ~20s)...")
    stop_times = pd.read_csv(os.path.join(dtc, "stop_times.txt"),
                             low_memory=False)
    stop_times.columns = stop_times.columns.str.strip().str.lower()

    # ── Sample one trip per route to keep graph manageable ──────────────────
    # Pick the first trip_id for each route — gives us full coverage of all
    # stops on every route without processing all 89k trips
    trip_route = dict(zip(trips["trip_id"], trips["route_id"]))
    one_trip_per_route = (trips.groupby("route_id")["trip_id"]
                               .first()
                               .values)
    print(f"[bus_graph] Sampling 1 trip per route -> {len(one_trip_per_route)} trips "
          f"out of {len(trips):,} total")

    sampled = stop_times[stop_times["trip_id"].isin(one_trip_per_route)]
    sampled = sampled.sort_values(["trip_id", "stop_sequence"])

    # Build lookups
    stop_names  = dict(zip(stops["stop_id"], stops["stop_name"]))
    stop_coords = dict(zip(stops["stop_id"],
                           zip(stops["stop_lat"], stops["stop_lon"])))

    G = nx.DiGraph()

    # Add all bus stops as nodes
    for _, row in stops.iterrows():
        node_id = f"bus:{row['stop_id']}"
        G.add_node(node_id,
                   name=row["stop_name"],
                   lat=float(row["stop_lat"]),
                   lon=float(row["stop_lon"]),
                   mode="bus")

    # Build edges
    edges_added   = 0
    edges_updated = 0

    for trip_id, group in sampled.groupby("trip_id"):
        rows = group.reset_index(drop=True)
        route_id = trip_route.get(trip_id, "unknown")

        for i in range(len(rows) - 1):
            curr = rows.iloc[i]
            nxt  = rows.iloc[i + 1]

            src = f"bus:{curr['stop_id']}"
            dst = f"bus:{nxt['stop_id']}"

            if src not in G or dst not in G:
                continue

            try:
                dep = _parse_time(curr["departure_time"])
                arr = _parse_time(nxt["arrival_time"])
                travel_time = max(arr - dep, 0.5)
            except Exception:
                continue

            if not G.has_edge(src, dst):
                G.add_edge(src, dst,
                           weight=travel_time,
                           mode="bus",
                           route_id=str(route_id),
                           from_stop=stop_names.get(curr["stop_id"], src),
                           to_stop=stop_names.get(nxt["stop_id"], dst))
                edges_added += 1
            elif G[src][dst]["weight"] > travel_time:
                G[src][dst]["weight"] = travel_time
                edges_updated += 1

    print(f"[bus_graph] {G.number_of_nodes():,} stops")
    print(f"[bus_graph] {G.number_of_edges():,} edges "
          f"({edges_added:,} added, {edges_updated:,} updated)")

    print("[bus_graph] Sample edges:")
    for src, dst, data in list(G.edges(data=True))[:5]:
        print(f"  {data['from_stop']:35s} -> {data['to_stop']:35s} "
              f"  {data['weight']:.1f} min  route {data['route_id']}")

    return G


if __name__ == "__main__":
    import os
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    G = build_bus_graph(data_dir)
    print(f"\nTotal nodes : {G.number_of_nodes():,}")
    print(f"Total edges : {G.number_of_edges():,}")
