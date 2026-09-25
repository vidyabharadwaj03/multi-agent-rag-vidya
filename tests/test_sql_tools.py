import pytest

from multiagent.sql_tools import UnsafeSQLError, get_schema_description, run_select, validate_select_only


def test_validate_select_only_accepts_select():
    assert validate_select_only("SELECT * FROM revenue") == "SELECT * FROM revenue"


def test_validate_select_only_rejects_non_select():
    with pytest.raises(UnsafeSQLError):
        validate_select_only("DROP TABLE revenue")


def test_validate_select_only_rejects_forbidden_keyword_in_select():
    with pytest.raises(UnsafeSQLError):
        validate_select_only("SELECT * FROM revenue WHERE 1=1; DELETE FROM revenue")


def test_validate_select_only_rejects_multiple_statements():
    with pytest.raises(UnsafeSQLError):
        validate_select_only("SELECT 1; SELECT 2")


def test_get_schema_description_excludes_internal_tables(test_db):
    schema = get_schema_description(test_db)
    assert "sqlite_" not in schema
    assert "revenue(" in schema
    assert "customers(" in schema
    assert "sales(" in schema
    assert "employee_satisfaction(" in schema


def test_run_select_returns_rows(test_db):
    columns, rows = run_select(test_db, "SELECT COUNT(*) as total FROM revenue")
    assert columns == ["total"]
    assert rows[0][0] > 0


def test_run_select_rejects_unsafe_query(test_db):
    with pytest.raises(UnsafeSQLError):
        run_select(test_db, "DELETE FROM revenue")
