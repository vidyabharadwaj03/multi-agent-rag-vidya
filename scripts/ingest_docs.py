import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from multiagent.config import get_settings
from multiagent.vector_store import VectorStore


def main():
    settings = get_settings()
    store = VectorStore(settings.chroma_persist_dir)
    count = store.ingest_directory(settings.docs_dir)
    print(f"Ingested {count} chunks into '{settings.chroma_persist_dir}'")


if __name__ == "__main__":
    main()
