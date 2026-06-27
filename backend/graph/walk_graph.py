import osmnx as ox
import networkx as nx

walk_speed = 4.5
drive_speed = 30

def build_walk_graph(data_dir: str) -> nx.DiGraph:
    G = ox.graph_from_place("Delhi,India", network_type="walk", simplify=True)
    A = nx.DiGraph()
    for node in G.nodes:
        node_id = f"walk:{node}"
        A.add_node(node_id,
                   name = f"walk junction {node}",
                   lat=float(G.nodes[node]["y"]),
                   lon=float(G.nodes[node]["x"]),
                   mode="walk")
    for u, v, data in G.edges(data=True):
        src = f"walk:{u}"
        dst = f"walk:{v}"
    
    # guard against list lengths
    length = data.get("length", 50)
    if isinstance(length, list):
        length = length[0]
    
    time_min = (length / 1000) / walk_speed * 60
    
    A.add_edge(src, dst,
               weight=time_min,
               mode="walk",
               from_stop=A.nodes[src]["name"] if "name" in A.nodes[src] else src,
               to_stop=A.nodes[dst]["name"] if "name" in A.nodes[dst] else dst)
    return A

def build_drive_graph(data_dir: str) -> nx.DiGraph:
    G = ox.graph_from_place("Delhi,India", network_type="drive", simplify=True)
    A = nx.DiGraph()
    for node in G.nodes:
        node_id = f"drive:{node}"
        A.add_node(node_id,
                   name = f"drive juntion {node}",
                   lat=float(G.nodes[node]["y"]),
                   lon=float(G.nodes[node]["x"]),
                   mode="drive")
    for u, v, data in G.edges(data=True):
        src = f"drive:{u}"
        dst = f"drive:{v}"

        # guard against list lengths
        length = data.get("length", 50)
        if isinstance(length, list):
            length = length[0]

        time_min = (length / 1000) / drive_speed * 60

        A.add_edge(src, dst,
                   weight=time_min,
                   mode="drive",
                   from_stop=A.nodes[src]["name"] if "name" in A.nodes[src] else src,
                   to_stop=A.nodes[dst]["name"] if "name" in A.nodes[dst] else dst)
    return A