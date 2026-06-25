"""
metro_graph.py — builds a directed NetworkX graph for the Delhi Metro.

Node ID format:  "metro:<stop_id>"
Edge attributes:
    weight      float   travel time in minutes
    mode        str     "metro"
    line        str     e.g. "Yellow Line"
    from_stop   str     human-readable name
    to_stop     str     human-readable name

Usage:
    from graph.metro_graph import build_metro_graph
    G = build_metro_graph("data/dmrc/stops.txt", "data/dmrc/stop_times.txt")
"""

import pandas as pd
import networkx as nx
from haversine import haversine, Unit


# Average metro speed km/h — used as fallback when stop_times lack real times
METRO_SPEED_KMH = 34

# Headway penalty added to every boarding event (average wait time)
HEADWAY_MINUTES = 4.0


def _parse_time(t: str) -> float:
    """Convert HH:MM:SS string to minutes. Handles times past midnight (e.g. 25:00:00)."""
    h, m, s = t.strip().split(":")
    return int(h) * 60 + int(m) + int(s) / 60


def build_metro_graph(stops_path: str, stop_times_path: str = None) -> nx.DiGraph:
    """
    Build metro graph from GTFS stops.txt and optionally stop_times.txt.
    If stop_times.txt is absent, falls back to haversine distance / speed estimate.
    """
    stops = pd.read_csv(stops_path)
    stops = stops.dropna(subset=["stop_lat", "stop_lon"])

    # Normalise column names to lowercase
    stops.columns = [c.strip().lower() for c in stops.columns]

    G = nx.DiGraph()

    # ── Add all stops as nodes ──────────────────────────────────────────────
    for _, row in stops.iterrows():
        node_id = f"metro:{row['stop_id']}"
        G.add_node(node_id,
                   name=row.get("stop_name", row["stop_id"]),
                   lat=float(row["stop_lat"]),
                   lon=float(row["stop_lon"]),
                   mode="metro",
                   line=row.get("route_id", row.get("line_name", "unknown")))

    # ── Add edges from stop_times.txt if available ──────────────────────────
    if stop_times_path:
        stop_times = pd.read_csv(stop_times_path, low_memory=False)
        stop_times.columns = [c.strip().lower() for c in stop_times.columns]
        stop_times = stop_times.sort_values(["trip_id", "stop_sequence"])

        for trip_id, group in stop_times.groupby("trip_id"):
            rows = group.reset_index(drop=True)
            for i in range(len(rows) - 1):
                curr = rows.iloc[i]
                nxt  = rows.iloc[i + 1]

                src = f"metro:{curr['stop_id']}"
                dst = f"metro:{nxt['stop_id']}"

                if src not in G or dst not in G:
                    continue

                try:
                    dep = _parse_time(str(curr["departure_time"]))
                    arr = _parse_time(str(nxt["arrival_time"]))
                    travel_time = max(arr - dep, 0.5)   # floor at 30 sec
                except Exception:
                    travel_time = _fallback_time(G, src, dst)

                # Only add edge if not already present (or if new time is faster)
                if not G.has_edge(src, dst) or G[src][dst]["weight"] > travel_time:
                    G.add_edge(src, dst,
                               weight=travel_time,
                               mode="metro",
                               from_stop=G.nodes[src]["name"],
                               to_stop=G.nodes[dst]["name"])

    else:
        # ── Fallback: connect stops that share a line in sequence ───────────
        # Requires stops.txt to have a 'line_name' or 'route_id' column
        # and stops ordered by sequence within each line.
        line_col = "line_name" if "line_name" in stops.columns else "route_id"
        if line_col in stops.columns:
            for line, group in stops.groupby(line_col):
                ordered = group.reset_index(drop=True)
                for i in range(len(ordered) - 1):
                    src_row = ordered.iloc[i]
                    dst_row = ordered.iloc[i + 1]
                    src = f"metro:{src_row['stop_id']}"
                    dst = f"metro:{dst_row['stop_id']}"
                    t   = _fallback_time(G, src, dst)
                    G.add_edge(src, dst, weight=t, mode="metro",
                               from_stop=src_row.get("stop_name", src),
                               to_stop=dst_row.get("stop_name", dst))
                    # Metro runs both directions
                    G.add_edge(dst, src, weight=t, mode="metro",
                               from_stop=dst_row.get("stop_name", dst),
                               to_stop=src_row.get("stop_name", src))

    print(f"[metro_graph] Built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def _fallback_time(G: nx.DiGraph, src: str, dst: str) -> float:
    """Estimate travel time from haversine distance at average metro speed."""
    src_data = G.nodes[src]
    dst_data = G.nodes[dst]
    dist_km = haversine(
        (src_data["lat"], src_data["lon"]),
        (dst_data["lat"], dst_data["lon"]),
        unit=Unit.KILOMETERS
    )
    return (dist_km / METRO_SPEED_KMH) * 60 + HEADWAY_MINUTES
