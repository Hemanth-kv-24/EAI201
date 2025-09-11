import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
import heapq

# Edges with arbitrary weights (you can adjust as per real distances)
edges = [
    ("Main Gate", "ID gate", 100),
    ("ID gate", "AC1", 80),
    ("AC1", "Lawn area", 60),
    ("AC1", "Library", 90),
    ("AC1", "ACB1-LW", 70),
    ("ACB1-LW", "Cafe", 40),
    ("Lawn area", "Library", 50),
    ("Lawn area", "Ac-Block2", 75),
    ("Ac-Block2", "Hostel", 85),
    ("Ac-Block2", "Food Court", 65),
    ("Hostel", "Sports Area", 100),
]

# Build adjacency list with weights
graph = {}
for u, v, w in edges:
    graph.setdefault(u, []).append((v, w))
    graph.setdefault(v, []).append((u, w))  # Undirected graph

def bfs(start, goal):
    queue = deque([[start]])
    visited = set()

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == goal:
            return path

        if node not in visited:
            visited.add(node)
            for neighbor, _ in graph.get(node, []):
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)
    return None

def dfs(start, goal):
    stack = [[start]]
    visited = set()

    while stack:
        path = stack.pop()
        node = path[-1]

        if node == goal:
            return path

        if node not in visited:
            visited.add(node)
            for neighbor, _ in graph.get(node, []):
                new_path = list(path)
                new_path.append(neighbor)
                stack.append(new_path)
    return None

def ucs(start, goal):
    pq = [(0, [start])]  # (cost, path)
    visited = set()

    while pq:
        cost, path = heapq.heappop(pq)
        node = path[-1]

        if node == goal:
            return path, cost

        if node not in visited:
            visited.add(node)
            for neighbor, weight in graph.get(node, []):
                if neighbor not in visited:
                    new_path = list(path)
                    new_path.append(neighbor)
                    heapq.heappush(pq, (cost + weight, new_path))
    return None, float('inf')

def draw_graph():
    G = nx.Graph()
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    # Manually positioned based on your diagram
    pos = {
        "Main Gate": (0, 0),
        "ID gate": (0, 1),
        "AC1": (0, 2),
        "ACB1-LW": (-1, 2.5),
        "Cafe": (-2, 2.5),
        "Lawn area": (0.5, 3),
        "Library": (1.5, 2.5),
        "Ac-Block2": (1, 4),
        "Hostel": (2, 4.5),
        "Food Court": (1, 4.8),
        "Sports Area": (2, 5.5)
    }

    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_color="lightgreen", node_size=3000, font_size=10, font_weight='bold')
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=9, font_color='black')

    plt.title("Campus Map", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def print_path(path, cost=None):
    if not path:
        print("No path found.")
    else:
        print("Path:")
        print(" -> ".join(path))
        if cost is not None:
            print(f"Total Distance: {cost} meters")

def main():
    print("Campus Pathfinding (Based on Map Diagram)")
    print("\nAvailable Locations:")
    for location in graph:
        print("-", location)

    start = input("\nEnter START location: ").strip()
    goal = input("Enter GOAL location: ").strip()

    if start not in graph or goal not in graph:
        print("Invalid location(s).")
        return

    print("\nChoose algorithm:")
    print("1. BFS")
    print("2. DFS")
    print("3. UCS")
    choice = input("Enter choice (1/2/3): ").strip()

    print("\nFinding path...\n")

    if choice == "1":
        path = bfs(start, goal)
        print("BFS Result:")
        print_path(path)
    elif choice == "2":
        path = dfs(start, goal)
        print("DFS Result:")
        print_path(path)
    elif choice == "3":
        path, cost = ucs(start, goal)
        print("UCS Result:")
        print_path(path, cost)
    else:
        print("Invalid choice.")

    # Visualize the graph
    draw_graph()

if __name__ == "__main__":
    main()

