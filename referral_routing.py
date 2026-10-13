
import heapq

def find_referral_route(graph, start, goal):
    queue = [(0, start, [start])]
    visited = set()

    while queue:
        cost, node, path = heapq.heappop(queue)

        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            return path, cost

        for neighbor, edge_cost in graph.get(node, {}).items():
            if edge_cost < 0:
                raise ValueError("Costs cannot be negative")
            if neighbor not in visited:
                heapq.heappush(
                    queue, (cost + edge_cost, neighbor, path + [neighbor])
                )

    return None, float("inf")


graph = {
    "Village Clinic": {"Community Health Centre": 3, "Town Hospital": 10},
    "Community Health Centre": {"Village Clinic": 3, "Town Hospital": 4},
    "Town Hospital": {"Village Clinic": 10, "Community Health Centre": 4}
}

path, cost = find_referral_route(graph, "Village Clinic", "Town Hospital")
print("Route:", " -> ".join(path) if path else "No route available")
print("Route cost:", cost)
