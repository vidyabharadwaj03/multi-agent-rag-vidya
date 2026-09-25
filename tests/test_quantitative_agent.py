from multiagent.quantitative_agent import QuantitativeAgent
from tests.fakes import FakeLLMClient


def test_answer_executes_generated_sql_and_summarizes(test_db):
    llm_client = FakeLLMClient(
        responses=[
            "SELECT region, SUM(amount) as total FROM revenue GROUP BY region",
            "North America leads in total revenue.",
        ]
    )
    agent = QuantitativeAgent(test_db, llm_client)

    result = agent.answer("Show me revenue by region")

    assert result.columns == ["region", "total"]
    assert len(result.rows) == 4
    assert result.summary == "North America leads in total revenue."
    assert len(llm_client.calls) == 2


def test_answer_rejects_unsafe_generated_sql(test_db):
    llm_client = FakeLLMClient(responses=["DELETE FROM revenue"])
    agent = QuantitativeAgent(test_db, llm_client)

    result = agent.answer("Delete everything")

    assert result.rows == []
    assert result.columns == []
    assert "rejected" in result.summary.lower()
    assert len(llm_client.calls) == 1


def test_answer_handles_empty_result_without_second_llm_call(test_db):
    llm_client = FakeLLMClient(
        responses=["SELECT * FROM revenue WHERE region = 'Nonexistent Region'"]
    )
    agent = QuantitativeAgent(test_db, llm_client)

    result = agent.answer("Show revenue for a region that does not exist")

    assert result.rows == []
    assert result.summary == "The query returned no results."
    assert len(llm_client.calls) == 1


def test_generate_sql_strips_markdown_fencing(test_db):
    llm_client = FakeLLMClient(responses=["```sql\nSELECT 1\n```", "One row returned."])
    agent = QuantitativeAgent(test_db, llm_client)

    result = agent.answer("Just give me 1")

    assert result.sql == "SELECT 1"
    assert result.rows == [[1]]
