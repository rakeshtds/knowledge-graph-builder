# Knowledge Graph Builder

Turn PDFs and web pages into a knowledge graph: documents are chunked, an LLM extracts entities and relationships, and the result is stored as a queryable graph you can visualize or export to Neo4j.

## Features

- Ingestion for PDF files (pypdf) and web pages (requests + BeautifulSoup text extraction)
- Overlapping text chunking tuned for extraction (configurable size/overlap)
- LLM entity/relationship extraction returning strict JSON triples with a type vocabulary
- Graph building with NetworkX: deduplication, entity normalization, degree/source tracking
- Exports: interactive `graph.html` (pyvis), plain JSON (nodes/edges), and Neo4j-ready Cypher script
- Provenance: every triple records the document and chunk it came from

## Architecture

`ingest.py` produces chunks with source metadata → `extract_graph.py` prompts the LLM per chunk and parses validated triples → `graph_store.py` merges triples into a NetworkX graph (normalizing entity names, counting evidence) → `visualize.py` writes HTML/JSON/Cypher exports.

## Tech Stack

Python 3.11 · NetworkX · pypdf · BeautifulSoup · pyvis · OpenAI-compatible LLM API

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
```

## Usage

```bash
# Build a graph from a PDF and a web page
python -m src.graph_store build --pdf paper.pdf --url https://example.com/about --out graph.json

# Export an interactive visualization and Neo4j Cypher
python -m src.visualize --graph graph.json --html graph.html --cypher import.cypher
```

## Example Output

See `sample/triples_example.json` for the extraction shape:

```json
{"subject": "Snowflake Cortex Analyst", "predicate": "GENERATES", "object": "SQL",
 "subject_type": "PRODUCT", "object_type": "TECHNOLOGY", "source": "paper.pdf", "chunk": 4}
```

## Project Structure

```
src/ingest.py         PDF / web ingestion and chunking
src/extract_graph.py  LLM triple extraction with JSON validation
src/graph_store.py    NetworkX graph build, dedupe, save/load, CLI
src/visualize.py      HTML visualization + JSON / Cypher export
sample/               Example triples
```

## Roadmap

- Embedding-based entity resolution for near-duplicate names
- GraphRAG query endpoint (natural-language questions over the graph)
- Incremental builds with chunk-level change detection

---

An original implementation built for portfolio purposes. Sample data is synthetic.
