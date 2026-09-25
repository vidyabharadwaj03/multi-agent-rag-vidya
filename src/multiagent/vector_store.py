import os
import re
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.utils import embedding_functions

COLLECTION_NAME = "enterprise_docs"


def chunk_document(text):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    buffer = ""
    for paragraph in paragraphs:
        if paragraph.startswith("#"):
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            buffer = paragraph
            continue
        candidate = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if len(candidate) > 800 and buffer:
            chunks.append(buffer.strip())
            buffer = paragraph
        else:
            buffer = candidate
    if buffer:
        chunks.append(buffer.strip())
    return chunks


class VectorStore:
    def __init__(self, persist_dir):
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def is_empty(self):
        return self._collection.count() == 0

    def ingest_directory(self, docs_dir):
        ids, documents, metadatas = [], [], []
        for path in sorted(Path(docs_dir).glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for i, chunk in enumerate(chunk_document(text)):
                ids.append(f"{path.stem}::chunk_{i}")
                documents.append(chunk)
                metadatas.append({"source": path.name, "chunk_index": i})

        if ids:
            self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)

    def query(self, query_text, k=4):
        results = self._collection.query(query_texts=[query_text], n_results=k)
        matches = []
        for doc_id, document, metadata, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            similarity = 1 - distance
            matches.append(
                {
                    "document_id": doc_id,
                    "source": metadata["source"],
                    "text": document,
                    "similarity_score": similarity,
                }
            )
        return matches
