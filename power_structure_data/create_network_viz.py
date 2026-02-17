#!/usr/bin/env python3
"""Create network visualization - requires networkx and matplotlib."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent


def create_d3_json():
    """Export nodes and edges as JSON for D3.js visualization."""
    import pandas as pd

    # Exclude non-person nodes (events, places, etc.)
    EXCLUDE = {"olympics", "summer", "winter", "war", "conference", "congress"}

    edges_path = DATA_DIR / "network_edges.csv"
    if not edges_path.exists():
        print("No network_edges.csv")
        return

    edges_df = pd.read_csv(edges_path)
    nodes = set()
    links = []
    for _, row in edges_df.iterrows():
        src, tgt = str(row["source"]), str(row["target"])
        if any(x in src.lower() for x in EXCLUDE) or any(x in tgt.lower() for x in EXCLUDE):
            continue
        nodes.add(src)
        nodes.add(tgt)
        links.append({"source": src, "target": tgt, "relationship": row.get("relationship", "")})

    nodes_list = [{"id": n, "name": n} for n in sorted(nodes)]
    graph = {"nodes": nodes_list, "links": links}
    out_path = DATA_DIR / "network_d3.json"
    out_path.write_text(json.dumps(graph, indent=2))
    print(f"Exported {len(nodes_list)} nodes, {len(links)} links to {out_path}")


def create_png():
    """Create PNG visualization with matplotlib."""
    try:
        import networkx as nx
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Install: pip install networkx matplotlib")
        return

    import pandas as pd
    edges_df = pd.read_csv(DATA_DIR / "network_edges.csv")
    G = nx.Graph()
    for _, row in edges_df.iterrows():
        G.add_edge(row["source"], row["target"])

    plt.figure(figsize=(20, 20))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    nx.draw_networkx(G, pos, node_size=20, font_size=6, with_labels=False)
    plt.savefig(DATA_DIR / "network_visualization.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved network_visualization.png: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


if __name__ == "__main__":
    create_d3_json()
    create_png()
