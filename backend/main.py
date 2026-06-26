from fastapi import FastAPI
from graph.graph_cache import load_graph
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import Request
from routing.dijkstra import dijkstra
from routing.bfs import fewest_transfers

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = load_graph()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "nodes" : app.state.graph.number_of_nodes()}
class RouteRequest(BaseModel):
    origin: str
    destination: str
    filter: str

@app.post("/route")
def get_route(request: Request, body: RouteRequest):
    G = request.app.state.graph
    if body.filter=="fastest":
        path ,cost= dijkstra(G, body.origin,body.destination)
        return {
            "cost": round(cost, 1),
            "path": [
                {
                    "name": G.nodes[node]["name"],
                    "mode": G.nodes[node]["mode"],
                    "lat":  G.nodes[node]["lat"],
                    "lon":  G.nodes[node]["lon"]
                }
                for node in path
            ]
        }    
    elif body.filter=="fewest_transfers":
        path,cost = fewest_transfers(G, body.origin, body.destination)
        return {
            "cost": round(cost, 1),
            "path": [
                {
                    "name": G.nodes[node]["name"],
                    "mode": G.nodes[node]["mode"],
                    "lat":  G.nodes[node]["lat"],
                    "lon":  G.nodes[node]["lon"]
                }
                for node in path
            ]
        }

