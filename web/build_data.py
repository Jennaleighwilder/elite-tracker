#!/usr/bin/env python3
"""Build combined JSON for web app from power_structure_data."""
import json
import csv
from pathlib import Path

DATA = Path(__file__).parent.parent / "power_structure_data"
OUT = Path(__file__).parent / "data"
OUT.mkdir(parents=True, exist_ok=True)

# Load network
with open(DATA / "network_d3.json") as f:
    network = json.load(f)

# Load cross-reference (high-value nodes)
cross_ref = set()
try:
    with open(DATA / "cross_reference.csv") as f:
        for row in csv.DictReader(f):
            cross_ref.add(row["name"].strip())
except Exception:
    pass

# Load skull bones for cohort/position
skull_data = {}
try:
    with open(DATA / "skull_bones_complete.csv") as f:
        for row in csv.DictReader(f):
            skull_data[row["name"].strip()] = {
                "cohort_year": row.get("cohort_year", ""),
                "position": row.get("position", "")[:150],
            }
except Exception:
    pass

# Enrich nodes
for node in network["nodes"]:
    name = node["id"]
    node["type"] = "policy" if name in cross_ref else "secret-society"
    node["connections"] = sum(1 for l in network["links"] if l["source"] == name or l["target"] == name)
    if name in skull_data:
        node["cohort_year"] = skull_data[name]["cohort_year"]
        node["position"] = skull_data[name]["position"]
    else:
        node["cohort_year"] = ""
        node["position"] = ""

# Convert links to edges format (source/target can be string ids, D3 will resolve)
edges = []
for link in network["links"]:
    rel = link.get("relationship", "connection")
    edge_type = "society-connection" if "Skull" in rel or "Bones" in rel else "policy-connection"
    edges.append({
        "source": link["source"],
        "target": link["target"],
        "type": edge_type,
        "weight": 3 if "Skull" in rel else 2,
        "relationship": rel,
    })

output = {
    "nodes": network["nodes"],
    "edges": edges,
}

with open(OUT / "network.json", "w") as f:
    json.dump(output, f, indent=0)

print(f"Built: {len(output['nodes'])} nodes, {len(output['edges'])} edges -> {OUT / 'network.json'}")
