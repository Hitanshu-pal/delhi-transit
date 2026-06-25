"""
graph_cache.py — builds the full multi-modal graph and saves it
as a pickle so FastAPI can load it instantly at startup.

Usage:
    python graph_cache.py          # build and save
    python graph_cache.py --test   # build, save, then run a test route
"""

import os
import pickle
import time
import networkx as nx

from metro_graph    import build_metro_graph
from bus_graph      import build_bus_graph
from transfer_graph import build_combined_graph

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "graph.pkl")
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")


def build_and_save():
    print("=" * 55)
    print("Building Delhi Transit multi-modal graph")
    print("=" * 55)

    t0 = time.time()

    print("\n[1/3] Building metro graph...")
    metro_G = build_metro_graph(DATA_DIR)

    print("\n[2/3] Building bus graph...")
    bus_G = build_bus_graph(DATA_DIR)

    print("\n[3/3] Merging and adding transfer edges...")
    G = build_combined_graph(metro_G, bus_G)

    print(f"\nSaving to {CACHE_PATH} ...")
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(G, f)

    elapsed = time.time() - t0
    size_mb = os.path.getsize(CACHE_PATH) / 1_000_000
    print(f"Done in {elapsed:.1f}s  |  cache size: {size_mb:.1f} MB")
    return G


def load_graph() -> nx.DiGraph:
    """Load cached graph. Rebuilds automatically if cache is missing."""
    if not os.path.exists(CACHE_PATH):
        print("[cache] No cache found — building now...")
        return build_and_save()

    print(f"[cache] Loading graph from {CACHE_PATH} ...")
    t0 = time.time()
    with open(CACHE_PATH, "rb") as f:
        G = pickle.load(f)
    print(f"[cache] Loaded in {time.time()-t0:.2f}s  "
          f"({G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges)")
    return G


if __name__ == "__main__":
    import sys
    G = build_and_save()

    if "--test" in sys.argv:
        print("\n--- Test route: Dilshad Garden -> Rajiv Chowk ---")
        # Find node IDs by name
        def find_node(name_fragment):
            for n, d in G.nodes(data=True):
                if name_fragment.lower() in d.get("name", "").lower():
                    return n
            return None

        src = find_node("Dilshad Garden")
        dst = find_node("Rajiv Chowk")

        if src and dst:
            path = nx.dijkstra_path(G, src, dst, weight="weight")
            cost = nx.dijkstra_path_length(G, src, dst, weight="weight")
            print(f"From : {G.nodes[src]['name']} ({src})")
            print(f"To   : {G.nodes[dst]['name']} ({dst})")
            print(f"Time : {cost:.1f} min")
            print(f"Stops: {len(path)}")
            print("Path:")
            for node in path:
                d = G.nodes[node]
                print(f"  [{d['mode']:5s}] {d['name']}")
        else:
            print(f"Could not find nodes: src={src}, dst={dst}")
