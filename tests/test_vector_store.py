from multiagent.vector_store import VectorStore, chunk_document


def test_chunk_document_splits_on_headings():
    text = "# Heading One\n\nParagraph one.\n\n# Heading Two\n\nParagraph two."
    chunks = chunk_document(text)
    assert len(chunks) == 2
    assert "Heading One" in chunks[0]
    assert "Heading Two" in chunks[1]


def test_vector_store_ingest_and_query(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "security.md").write_text(
        "# Security Policy\n\nAll employees must use multi-factor authentication."
    )
    (docs_dir / "reviews.md").write_text(
        "# Code Review\n\nEvery pull request needs at least one approval."
    )

    store = VectorStore(str(tmp_path / "chroma"))
    count = store.ingest_directory(str(docs_dir))
    assert count == 2

    results = store.query("What authentication is required?", k=2)
    assert results[0]["source"] == "security.md"
    assert results[0]["similarity_score"] > results[1]["similarity_score"]


def test_vector_store_is_empty_before_ingestion(tmp_path):
    store = VectorStore(str(tmp_path / "chroma"))
    assert store.is_empty()
