from haversine import haversine, Unit

def nearest_stop(G,lat:float , lon:float,mode:str = None):
    min_dist = float('inf')
    nearest_node = None
    for node in G.nodes:
        if mode and G.nodes[node]['mode'] != mode:
            continue
        node_lat = G.nodes[node]['lat']
        node_lon = G.nodes[node]['lon']
        dist = haversine((lat, lon), (node_lat, node_lon), unit=Unit.METERS)
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
    return nearest_node, min_dist