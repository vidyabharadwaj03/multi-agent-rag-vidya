import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from scripts.build_database import build as build_database


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test_enterprise.db"
    build_database(db_path)
    return str(db_path)
