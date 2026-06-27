import httpx
import networkx as nx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from thefuzz import process
from graph.graph_cache import load_graph
from routing.geocode import nearest_stop
from routing.dijkstra import dijkstra
from routing.bfs import fewest_transfers

def get_path_with_routes(G, path):
    result = []
    for i, node in enumerate(path):
        stop = {
            "name": G.nodes[node]["name"],
            "mode": G.nodes[node]["mode"],
            "lat":  G.nodes[node]["lat"],
            "lon":  G.nodes[node]["lon"],
            "route_id": None
        }
        # look at edge leaving this node (forward) for first stop
        # look at edge entering this node (backward) for all others
        if i < len(path) - 1:
            next_node = path[i + 1]
            if G.has_edge(node, next_node):
                stop["route_id"] = G[node][next_node].get("route_id")
        else:
            prev = path[i - 1]
            if G.has_edge(prev, node):
                stop["route_id"] = G[prev][node].get("route_id")
        result.append(stop)
    for stop in result:
        print(stop["name"], stop["route_id"])
    return result

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = load_graph()
    G = app.state.graph
    app.state.stop_index = {G.nodes[n]["name"]: n for n in app.state.graph.nodes}
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
def health():
    return {"status": "ok", "nodes" : app.state.graph.number_of_nodes()}
class RouteRequest(BaseModel):
    origin: str | None = None          # node ID like "metro:50"
    destination: str | None = None     
    origin_lat: float | None = None    # or coordinates
    origin_lon: float | None = None
    dest_lat: float | None = None
    dest_lon: float | None = None
    mode: str

@app.post("/route")
def get_route(request: Request, body: RouteRequest):
    G = request.app.state.graph

    # resolve origin and destination to node IDs
    if body.origin and body.destination:
        origin_node = body.origin
        dest_node   = body.destination
    elif body.origin_lat and body.origin_lon and body.dest_lat and body.dest_lon:
        origin_node, _ = nearest_stop(G, body.origin_lat, body.origin_lon)
        dest_node,   _ = nearest_stop(G, body.dest_lat,   body.dest_lon)
    else:
        return {"error": "provide either node IDs or coordinates"}

    # pick graph and algorithm based on filter
    if body.mode == "fastest":
        path, cost = dijkstra(G, origin_node, dest_node)

    elif body.mode == "fewest_transfers":
        path, cost = fewest_transfers(G, origin_node, dest_node)

    elif body.mode == "metro_only":
        sub = nx.subgraph_view(G,
            filter_node=lambda n: G.nodes[n].get("mode") in {"metro"})
        origin_node, _ = nearest_stop(G, body.origin_lat or G.nodes[origin_node]["lat"],
                                     body.origin_lon or G.nodes[origin_node]["lon"], mode="metro")
        dest_node, _   = nearest_stop(G, body.dest_lat or G.nodes[dest_node]["lat"],
                                     body.dest_lon or G.nodes[dest_node]["lon"], mode="metro")
        path, cost = dijkstra(sub, origin_node, dest_node)

    elif body.mode == "bus_only":
        sub = nx.subgraph_view(G,
            filter_node=lambda n: G.nodes[n].get("mode") in {"bus"})
        origin_node, _ = nearest_stop(G, body.origin_lat or G.nodes[origin_node]["lat"],
                                     body.origin_lon or G.nodes[origin_node]["lon"], mode="bus")
        dest_node, _   = nearest_stop(G, body.dest_lat or G.nodes[dest_node]["lat"],
                                     body.dest_lon or G.nodes[dest_node]["lon"], mode="bus")
        path, cost = dijkstra(sub, origin_node, dest_node)

    return {
        "cost": round(cost, 1),
        "path": get_path_with_routes(G, path)
            }
@app.get("/stops")
def search_stops(request: Request, q: str):
    G = request.app.state.graph
    index = request.app.state.stop_index
    matches= process.extract(q, index.keys(), limit = 5)
    return [
            {
                "id": index[name],
                "name": name,
                "mode": G.nodes[index[name]]["mode"],
                "lat":  G.nodes[index[name]]["lat"],
                "lon":  G.nodes[index[name]]["lon"]
            }
            for name, score in matches
    ]
@app.get("/geocode")
async def geocode(request: Request, address: str):
    G = request.app.state.graph
    
    # call nominatim - free OSM geocoding, no key needed
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address + ", Delhi, India", "format": "json", "limit": 1}
    headers = {"User-Agent": "delhi-transit-planner"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=headers)
        results = resp.json()
    
    if not results:
        return {"error": "address not found"}
    
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    nearest_node, dist_m = nearest_stop(G, lat, lon)
    
    return {
        "lat": lat,
        "lon": lon,
        "nearest_stop": nearest_node,
        "stop_name": G.nodes[nearest_node]["name"],
        "stop_mode": G.nodes[nearest_node]["mode"],
        "walk_distance_m": round(dist_m)
    }