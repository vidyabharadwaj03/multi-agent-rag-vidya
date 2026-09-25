import re
import sqlite3

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|PRAGMA|REPLACE|VACUUM)\b",
    re.IGNORECASE,
)


class UnsafeSQLError(Exception):
    pass


def validate_select_only(sql):
    stripped = sql.strip().rstrip(";")
    if not stripped.lower().startswith("select"):
        raise UnsafeSQLError("Only SELECT statements are allowed")
    if FORBIDDEN_KEYWORDS.search(stripped):
        raise UnsafeSQLError("Query contains a disallowed keyword")
    if ";" in stripped:
        raise UnsafeSQLError("Multiple statements are not allowed")
    return stripped


def get_schema_description(db_path):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        lines = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [f"{row[1]} {row[2]}" for row in cursor.fetchall()]
            lines.append(f"{table}({', '.join(columns)})")
        return "\n".join(lines)
    finally:
        conn.close()


def run_select(db_path, sql):
    sql = validate_select_only(sql)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [description[0] for description in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]
        return columns, rows
    finally:
        conn.close()
