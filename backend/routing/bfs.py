import heapq
import networkx as nx

def fewest_transfers(G, start, end):
    pq = [(0,start)]
    distances = {node: float('inf') for node in G}
    previous= {node: None for node in G}

    distances[start] = 0
    while pq:
        current_distance, current_node = heapq.heappop(pq)

        if current_node == end:
            break
        for neighbor in G.neighbors(current_node):
            weight = 0 if G[current_node][neighbor]['mode']==G.nodes[current_node]['mode'] else 1
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current_node
                heapq.heappush(pq, (distance, neighbor))
    path = []
    node = end
    while node:
        path.append(node)
        node = previous[node]
    path.reverse()
    return path, distances[end]