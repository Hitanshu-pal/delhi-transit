import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),"graph"))
sys.path.append(os.path.join(os.path.dirname(__file__),"routing"))

from graph_cache import load_graph
from bfs import fewest_transfers
from dijkstra import dijkstra
G=load_graph()
src="metro:1"
dst = "bus:800"
path,cost=fewest_transfers(G,src,dst)
print(f"Time: {cost:.1f}min")
print(f"Stops:{len(path)}")
for node in path:
    d = G.nodes[node]
    print(f"[{d['mode']:5s}]{d['name']}")
