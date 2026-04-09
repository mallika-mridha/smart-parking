from flask import Flask, jsonify, request
import csv
import os
from astar import astar, haversine

app = Flask(__name__)

CSV_FILE = 'campus_graph.csv'

nodes = {}
graph = {}
parking_nodes = set()

def load_csv():
    global nodes, graph, parking_nodes
    nodes = {}
    graph = {}
    parking_nodes = set()

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found in {os.getcwd()}")

    # -------- FIRST PASS: Load nodes --------
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')  # ✅ FIXED
        for row in reader:
            name = row.get('Node', '').strip()
            if not name:
                continue

            try:
                lat = float(row.get('Latitude', '0') or 0)
                lon = float(row.get('Longitude', '0') or 0)
            except ValueError:
                continue

            desc = row.get('Description', '') or ''
            type_ = row.get('type', '') or ''
            label = row.get('label', '') or ''

            nodes[name] = {
                'lat': lat,
                'lon': lon,
                'desc': desc,
                'type': type_,
                'label': label
            }

            # ✅ FIXED parking detection
            if type_.strip().lower() == "parking":
                parking_nodes.add(name)

    # -------- SECOND PASS: Build graph --------
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')  # ✅ FIXED
        for row in reader:
            n1 = row.get('Node', '').strip()
            n2 = (row.get('Connected_to') or '').strip()

            if not n1 or not n2:
                continue

            try:
                dist = float(row.get('Distance (m)', '0') or 0)
            except ValueError:
                dist = 0.0

            graph.setdefault(n1, [])
            graph.setdefault(n2, [])

            # undirected graph
            graph[n1].append({'node': n2, 'dist': dist})
            graph[n2].append({'node': n1, 'dist': dist})


# Load data once
load_csv()


@app.route('/')
def home():
    return "Smart Parking Backend Running 🚀"


def get_parking_route(start, index):
    results = []

    for p in parking_nodes:
        path, dist = astar(graph, start, p, nodes)
        if path is not None:
            results.append((dist, path, p))

    results.sort(key=lambda x: x[0])

    if index >= len(results):
        return None, None, None

    dist, path, parking = results[index]
    return path, dist, parking


@app.route("/nearest_parking")
def nearest_parking():
    start = request.args.get("start")
    index = int(request.args.get("index", 0))

    if start not in nodes:
        return jsonify({"error": "Invalid start node"}), 400

    path, dist, parking = get_parking_route(start, index)

    if path is None:
        return jsonify({"error": "No more parking spots"}), 404

    coords = [{"lat": nodes[n]["lat"], "lng": nodes[n]["lon"]} for n in path]

    return jsonify({
        "coords": coords,
        "distance": dist,
        "parking": parking,
        "index": index
    })


@app.route('/graph-data')
def graph_data():
    edges = []
    seen = set()

    for u, neighbors in graph.items():
        for nb in neighbors:
            v = nb['node']
            key = tuple(sorted([u, v]))

            if key in seen:
                continue
            seen.add(key)

            if u in nodes and v in nodes:
                coords = [
                    [nodes[u]['lat'], nodes[u]['lon']],
                    [nodes[v]['lat'], nodes[v]['lon']]
                ]
            else:
                coords = [None, None]

            edges.append({
                'from': u,
                'to': v,
                'distance': nb['dist'],
                'coords': coords
            })

    visible_nodes = {
        k: v for k, v in nodes.items()
        if v.get('type') in {'normal', 'parking'}
    }

    return jsonify({
        'nodes': visible_nodes,
        'edges': edges
    })


# ✅ FIXED for deployment (Render)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
