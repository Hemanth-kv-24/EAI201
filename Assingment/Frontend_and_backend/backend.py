from flask import Flask, render_template, request, jsonify
from collections import deque
import heapq

app = Flask(__name__)

# Updated edges based on your second graph
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

# Build the graph
graph = {}
for u, v, w in edges:
    graph.setdefault(u, []).append((v, w))
    graph.setdefault(v, []).append((u, w))

def bfs(start, goal):
    if start not in graph or goal not in graph:
        return None
    
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
                if neighbor not in visited:
                    queue.append(path + [neighbor])
    return None

def dfs(start, goal):
    if start not in graph or goal not in graph:
        return None
    
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
                if neighbor not in visited:
                    stack.append(path + [neighbor])
    return None

def ucs(start, goal):
    if start not in graph or goal not in graph:
        return None, float('inf')
    
    pq = [(0, [start])]
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
                    heapq.heappush(pq, (cost + weight, path + [neighbor]))
    return None, float('inf')

@app.route("/")
def index():
    locations = sorted(graph.keys())
    return render_template("index.html", locations=locations)

@app.route("/find_path", methods=["POST"])
def find_path():
    data = request.get_json()
    start = data.get("start")
    goal = data.get("goal")
    algo = data.get("algorithm")
    
    if not start or not goal or not algo:
        return jsonify({"error": "Missing parameters"}), 400
    
    if start not in graph or goal not in graph:
        return jsonify({"error": "Invalid locations"}), 400
    
    if algo == "bfs":
        path = bfs(start, goal)
        cost = None
    elif algo == "dfs":
        path = dfs(start, goal)
        cost = None
    elif algo == "ucs":
        path, cost = ucs(start, goal)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400
    
    if path:
        return jsonify({
            "path": path,
            "cost": cost,
            "success": True
        })
    else:
        return jsonify({
            "path": [],
            "cost": None,
            "success": False,
            "error": "No path found"
        })

if __name__ == "__main__":
    app.run(debug=True)
