"""Exports: interactive HTML visualization, JSON, and Neo4j Cypher.

Usage:
    python -m src.visualize --graph graph.json --html graph.html --cypher import.cypher
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_store import load_graph  # noqa: E402


def export_html(graph, path: str) -> None:
    from pyvis.network import Network

    net = Network(height="800px", width="100%", directed=True, notebook=False)
    for node, data in graph.nodes(data=True):
        net.add_node(node, label=data.get("label", node),
                     title=f"{data.get('type', '')} · mentioned {data.get('mentions', 0)}x")
    for subj, obj, data in graph.edges(data=True):
        net.add_edge(subj, obj, label=data.get("predicate", ""), title=f"evidence: {data.get('evidence', 1)}")
    net.write_html(path)


def export_json(graph, path: str) -> None:
    nodes = [{"id": n, **{k: v for k, v in d.items()}} for n, d in graph.nodes(data=True)]
    edges = [
        {"subject": s, "object": o, "predicate": d.get("predicate"), "sources": d.get("sources", [])}
        for s, o, d in graph.edges(data=True)
    ]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"nodes": nodes, "edges": edges}, fh, indent=2)


def _cypher_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def export_cypher(graph, path: str) -> None:
    """Neo4j import script using MERGE so re-runs are idempotent."""
    lines = []
    for node, data in graph.nodes(data=True):
        label = _cypher_escape(str(data.get("type", "Entity")).title())
        name = _cypher_escape(str(data.get("label", node)))
        lines.append(f"MERGE (n:{label} {{name: '{name}'}});")
    for subj, obj, data in graph.edges(data=True):
        s_label = _cypher_escape(str(graph.nodes[subj].get("label", subj)))
        o_label = _cypher_escape(str(graph.nodes[obj].get("label", obj)))
        pred = str(data.get("predicate", "RELATED_TO")).replace(" ", "_")
        lines.append(
            f"MATCH (a {{name: '{s_label}'}}), (b {{name: '{o_label}'}}) "
            f"MERGE (a)-[:{pred}]->(b);"
        )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a knowledge graph")
    parser.add_argument("--graph", default="graph.json")
    parser.add_argument("--html")
    parser.add_argument("--json")
    parser.add_argument("--cypher")
    args = parser.parse_args()

    graph = load_graph(args.graph)
    if args.html:
        export_html(graph, args.html)
        print(f"Wrote {args.html}")
    if args.json:
        export_json(graph, args.json)
        print(f"Wrote {args.json}")
    if args.cypher:
        export_cypher(graph, args.cypher)
        print(f"Wrote {args.cypher}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
