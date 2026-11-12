"""Graph construction with NetworkX: merge triples, dedupe, persist.

CLI:
    python -m src.graph_store build --pdf a.pdf --url https://... --out graph.json
    python -m src.graph_store stats --graph graph.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def normalize(name: str) -> str:
    """Canonical entity key: lowercase, collapsed whitespace, stripped punctuation."""
    return re.sub(r"\s+", " ", name.strip().lower()).strip(".")


def build_graph(triples: list[dict]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for triple in triples:
        subj_key, obj_key = normalize(triple["subject"]), normalize(triple["object"])
        for key, label, etype in (
            (subj_key, triple["subject"], triple["subject_type"]),
            (obj_key, triple["object"], triple["object_type"]),
        ):
            if key not in graph:
                graph.add_node(key, label=label, type=etype, mentions=0)
            graph.nodes[key]["mentions"] += 1
        predicate = triple["predicate"].upper()
        existing = [
            data for _, _, data in graph.edges[subj_key][obj_key].values()
            if data.get("predicate") == predicate
        ] if graph.has_edge(subj_key, obj_key) else []
        if existing:
            existing[0]["evidence"] += 1
            existing[0]["sources"] = sorted(set(existing[0]["sources"] + [triple["source"]]))
        else:
            graph.add_edge(
                subj_key, obj_key, predicate=predicate, evidence=1,
                sources=[triple["source"]],
            )
    return graph


def save_graph(graph: nx.MultiDiGraph, path: str) -> None:
    data = nx.node_link_data(graph, edges="edges")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_graph(path: str) -> nx.MultiDiGraph:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return nx.node_link_graph(data, edges="edges")


def graph_stats(graph: nx.MultiDiGraph) -> dict:
    predicates: dict[str, int] = {}
    for _, _, data in graph.edges(data=True):
        predicates[data["predicate"]] = predicates.get(data["predicate"], 0) + 1
    top = sorted(graph.nodes(data=True), key=lambda kv: kv[1].get("mentions", 0), reverse=True)[:5]
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "predicates": predicates,
        "most_mentioned": [(data["label"], data["mentions"]) for _, data in top],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Knowledge graph builder")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--pdf", action="append", default=[])
    build.add_argument("--url", action="append", default=[])
    build.add_argument("--out", default="graph.json")

    stats = sub.add_parser("stats")
    stats.add_argument("--graph", default="graph.json")

    args = parser.parse_args()
    if args.command == "build":
        from extract_graph import extract_from_chunks
        from ingest import ingest

        sources = [("pdf", p) for p in args.pdf] + [("url", u) for u in args.url]
        if not sources:
            print("Provide at least one --pdf or --url", file=sys.stderr)
            return 1
        chunks = ingest(sources)
        print(f"Ingested {len(chunks)} chunks; extracting triples...")
        triples = extract_from_chunks(chunks)
        graph = build_graph(triples)
        save_graph(graph, args.out)
        print(f"Saved {args.out}: {json.dumps(graph_stats(graph))}")
    elif args.command == "stats":
        print(json.dumps(graph_stats(load_graph(args.graph)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
