from multiagent.logging_config import Timer, get_logger, log_event
from multiagent.schemas import QuantitativeResult
from multiagent.sql_tools import UnsafeSQLError, get_schema_description, run_select


class QuantitativeAgent:
    def __init__(self, db_path, llm_client):
        self.db_path = db_path
        self.llm_client = llm_client
        self.schema = get_schema_description(db_path)
        self.logger = get_logger("quantitative_agent")

    def _generate_sql(self, query):
        prompt = (
            f"Database schema:\n{self.schema}\n\n"
            f"Question: {query}\n\n"
            "Write a single SQLite SELECT query that answers the question. "
            "Output only the SQL query, with no explanation, no markdown formatting, "
            "and no trailing semicolon."
        )
        raw_sql = self.llm_client.complete(
            prompt,
            system="You translate natural language questions into SQLite SELECT queries.",
        )
        return raw_sql.strip().strip("`").replace("sql\n", "", 1).strip()

    def answer(self, query):
        with Timer() as timer:
            sql = self._generate_sql(query)
            try:
                columns, rows = run_select(self.db_path, sql)
                error = None
            except UnsafeSQLError as exc:
                columns, rows = [], []
                error = str(exc)

        log_event(
            self.logger,
            "sql_generated",
            query=query,
            sql=sql,
            row_count=len(rows),
            error=error,
            execution_time_seconds=round(timer.elapsed_seconds, 4),
        )

        if error:
            return QuantitativeResult(
                sql=sql,
                columns=[],
                rows=[],
                summary=f"The generated query was rejected for safety reasons: {error}",
            )

        summary = self._summarize(query, columns, rows)
        return QuantitativeResult(sql=sql, columns=columns, rows=rows, summary=summary)

    def _summarize(self, query, columns, rows):
        if not rows:
            return "The query returned no results."

        preview_rows = rows[:15]
        table_preview = ", ".join(columns) + "\n" + "\n".join(
            ", ".join(str(value) for value in row) for row in preview_rows
        )
        prompt = (
            f"Question: {query}\n\n"
            f"Query result ({len(rows)} row(s), showing up to 15):\n{table_preview}\n\n"
            "Write a short, plain-language summary of what this result shows."
        )
        return self.llm_client.complete(
            prompt, system="You summarize SQL query results in plain language."
        )
