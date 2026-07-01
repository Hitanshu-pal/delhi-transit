"""
metro_graph.py — builds a directed NetworkX graph for the Delhi Metro
from the OTD GTFS feed.

Node ID format : "metro:<stop_id>"
Edge attributes:
    weight      float   travel time in minutes (departure to arrival)
    mode        str     "metro"
    route_id    str     e.g. "1" (matches routes.txt)
    from_stop   str     human-readable station name
    to_stop     str     human-readable station name
"""

import pandas as pd
import networkx as nx


HEADWAY_MINUTES = 4.0   # average wait to board (added once per trip leg)


def _parse_time(t: str) -> float:
    """HH:MM:SS -> minutes. Handles post-midnight times like 25:00:00."""
    h, m, s = str(t).strip().split(":")
    return int(h) * 60 + int(m) + int(s) / 60


def build_metro_graph(data_dir: str) -> nx.DiGraph:
    """
    Build metro graph from GTFS files in data_dir/dmrc/.

    Args:
        data_dir: path to the backend/data folder

    Returns:
        nx.DiGraph with time-cost edges
    """
    import os
    dmrc = os.path.join(data_dir, "dmrc")

    stops      = pd.read_csv(os.path.join(dmrc, "stops.txt"))
    trips      = pd.read_csv(os.path.join(dmrc, "trips.txt"))
    stop_times = pd.read_csv(os.path.join(dmrc, "stop_times.txt"),
                             low_memory=False)

    # Normalise column names
    stops.columns      = stops.columns.str.strip().str.lower()
    trips.columns      = trips.columns.str.strip().str.lower()
    stop_times.columns = stop_times.columns.str.strip().str.lower()

    # Build stop_id -> name lookup
    stop_names = dict(zip(stops["stop_id"], stops["stop_name"]))
    stop_coords = dict(zip(stops["stop_id"],
                           zip(stops["stop_lat"], stops["stop_lon"])))

    # Build trip_id -> route_id lookup
    trip_route = dict(zip(trips["trip_id"], trips["route_id"]))
    trip_shape = dict(zip(trips["trip_id"], trips["shape_id"]))

    G = nx.DiGraph()

    # Add all metro stations as nodes
    for _, row in stops.iterrows():
        node_id = f"metro:{row['stop_id']}"
        G.add_node(node_id,
                   name=row["stop_name"],
                   lat=float(row["stop_lat"]),
                   lon=float(row["stop_lon"]),
                   mode="metro")

    # Sort stop_times and build edges trip by trip
    stop_times = stop_times.sort_values(["trip_id", "stop_sequence"])

    edges_added = 0
    edges_updated = 0

    for trip_id, group in stop_times.groupby("trip_id"):
        rows = group.reset_index(drop=True)
        route_id = trip_route.get(trip_id, "unknown")

        for i in range(len(rows) - 1):
            curr = rows.iloc[i]
            nxt  = rows.iloc[i + 1]

            src = f"metro:{curr['stop_id']}"
            dst = f"metro:{nxt['stop_id']}"

            if src not in G or dst not in G:
                continue

            try:
                dep = _parse_time(curr["departure_time"])
                arr = _parse_time(nxt["arrival_time"])
                travel_time = max(arr - dep, 0.3)   # floor at 18 seconds
            except Exception:
                continue

            # Keep the fastest known time for this edge across all trips
            if not G.has_edge(src, dst):
                shape_id = trip_shape.get(trip_id, None)

                G.add_edge(src, dst,
                        weight=travel_time,
                        mode="metro",
                        route_id=str(route_id),
                        shape_id=str(shape_id) if shape_id else None,
                        from_stop=stop_names.get(curr["stop_id"], src),
                        to_stop=stop_names.get(nxt["stop_id"], dst))
                edges_added += 1
            elif G[src][dst]["weight"] > travel_time:
                G[src][dst]["weight"] = travel_time
                edges_updated += 1

    print(f"[metro_graph] {G.number_of_nodes()} stations")
    print(f"[metro_graph] {G.number_of_edges()} edges "
          f"({edges_added} added, {edges_updated} updated to faster time)")

    # Quick sanity check — print 5 sample edges
    print("[metro_graph] Sample edges:")
    for src, dst, data in list(G.edges(data=True))[:5]:
        print(f"  {data['from_stop']:30s} -> {data['to_stop']:30s} "
              f"  {data['weight']:.1f} min")

    return G


if __name__ == "__main__":
    import os
    # Run directly to test: python metro_graph.py
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    G = build_metro_graph(data_dir)
    print(f"\nTotal nodes : {G.number_of_nodes()}")
    print(f"Total edges : {G.number_of_edges()}")
    print(f"\nAvg travel time per edge: "
          f"{sum(d['weight'] for _,_,d in G.edges(data=True)) / G.number_of_edges():.1f} min")
