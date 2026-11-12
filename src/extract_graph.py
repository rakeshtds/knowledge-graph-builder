"""LLM entity/relationship extraction into validated triples."""
from __future__ import annotations

import json
import os

ENTITY_TYPES = ["PERSON", "ORGANIZATION", "PRODUCT", "TECHNOLOGY", "CONCEPT", "PLACE", "EVENT"]

PROMPT = """Extract factual relationships from the text as knowledge-graph triples.
Return ONLY a JSON array; each item:
{{"subject": "...", "subject_type": one of {types}, "predicate": "UPPER_SNAKE_CASE verb phrase",
  "object": "...", "object_type": one of {types}}}
Rules: use canonical entity names (no pronouns); keep predicates short
(e.g. WORKS_AT, USES, INTEGRATES_WITH, DEPENDS_ON); skip opinions and vague claims.

Text:
{text}
"""


def _valid(item: dict) -> bool:
    keys = {"subject", "subject_type", "predicate", "object", "object_type"}
    return keys.issubset(item) and item["subject_type"] in ENTITY_TYPES and item["object_type"] in ENTITY_TYPES


def extract_triples(chunk_text: str, source: str, chunk_index: int, model: str | None = None) -> list[dict]:
    """Extract triples from one chunk; returns [] on parse/validation failure."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model or os.environ.get("KG_LLM_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": PROMPT.format(types=ENTITY_TYPES, text=chunk_text)
                   + '\nWrap the array as {"triples": [...]}.',
        }],
        temperature=0,
    )
    try:
        payload = json.loads(response.choices[0].message.content)
        items = payload.get("triples", [])
    except (json.JSONDecodeError, AttributeError):
        return []
    triples = []
    for item in items:
        if isinstance(item, dict) and _valid(item):
            item["source"] = source
            item["chunk"] = chunk_index
            triples.append(item)
    return triples


def extract_from_chunks(chunks, model: str | None = None) -> list[dict]:
    """Run extraction over all chunks (sequentially; batch in real deployments)."""
    all_triples: list[dict] = []
    for chunk in chunks:
        all_triples.extend(extract_triples(chunk.text, chunk.source, chunk.index, model=model))
    return all_triples
