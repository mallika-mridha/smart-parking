# a_star.py
import math
import heapq



def haversine(a, b):

    if isinstance(a, dict):
        lat1, lon1 = a['lat'], a['lon']
    else:
        lat1, lon1 = a
    if isinstance(b, dict):
        lat2, lon2 = b['lat'], b['lon']
    else:
        lat2, lon2 = b

    # convert to radians
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a_hav = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a_hav), math.sqrt(1 - a_hav))
    d = R * c
    return d

def astar(graph, start, goal, nodes, heuristic=haversine):

    # Priority queue: (f_score, g_score, node, parent)
    assert start in nodes, f"{start} missing from nodes"
    assert goal in nodes, f"{goal} missing from nodes"
    open_heap = []
    heapq.heappush(open_heap, (0.0, 0.0, start, None))

    came_from = {}           # node -> parent
    g_score = {start: 0.0}   # cost from start to node
    f_score = {start: heuristic(nodes[start], nodes[goal])}
    
    closed = set()

    while open_heap:
        f, g, current, parent = heapq.heappop(open_heap)

        if current in closed:
            continue

        came_from[current] = parent

        if current == goal:
            # reconstruct path
            path = []
            node = current
            total = g_score[current]
            while node is not None:
                path.append(node)
                node = came_from.get(node)
            path.reverse()
            return path, total

        closed.add(current)

        neighbors = graph.get(current, [])
        for nb in neighbors:
            neighbor = nb['node']
            dist = float(nb['dist'] or 0.0)  # cost to neighbor (meters)
            tentative_g = g_score[current] + dist

            if neighbor in closed:
                # maybe a better path exists from another node
                if tentative_g >= g_score.get(neighbor, float('inf')):
                    continue

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                h = heuristic(nodes[neighbor], nodes[goal])
                f_new = tentative_g + h
                heapq.heappush(open_heap, (f_new, tentative_g, neighbor, current))
                f_score[neighbor] = f_new

    return None, None
