"""Document ingestion: PDFs and web pages -> overlapping text chunks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    index: int


def chunk_text(text: str, source: str, size: int = 1200, overlap: int = 200) -> list[Chunk]:
    """Split text into overlapping character chunks at word boundaries."""
    words = text.split()
    chunks: list[Chunk] = []
    step_words = max(1, (size - overlap) // 6)  # ~6 chars per word heuristic
    words_per_chunk = max(step_words + overlap // 6, 1)
    for start in range(0, len(words), step_words):
        piece = " ".join(words[start:start + words_per_chunk])
        if piece.strip():
            chunks.append(Chunk(text=piece, source=source, index=len(chunks)))
        if start + words_per_chunk >= len(words):
            break
    return chunks


def read_pdf(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def read_url(url: str) -> str:
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url, timeout=30, headers={"User-Agent": "kg-builder/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def ingest(sources: list[tuple[str, str]]) -> list[Chunk]:
    """sources: list of ("pdf"|"url", location). Returns all chunks."""
    all_chunks: list[Chunk] = []
    for kind, location in sources:
        text = read_pdf(location) if kind == "pdf" else read_url(location)
        all_chunks.extend(chunk_text(text, source=location))
    return all_chunks
