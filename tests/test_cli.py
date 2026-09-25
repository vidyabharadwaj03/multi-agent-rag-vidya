from multiagent.cli import format_response
from multiagent.schemas import AgentAnswer, Citation, ManagerResponse, QualitativeResult, QuantitativeResult


def test_format_response_shows_clarification():
    response = ManagerResponse(
        query="tell me stuff",
        classification="AMBIGUOUS",
        clarification_question="What do you mean by 'stuff'?",
        final_answer="What do you mean by 'stuff'?",
    )
    output = format_response(response)
    assert "What do you mean by 'stuff'?" in output
    assert "AMBIGUOUS" in output


def test_format_response_shows_qualitative_citations():
    qualitative = QualitativeResult(
        answer="MFA is required.",
        citations=[
            Citation(
                document_id="security_policy::chunk_0",
                source="security_policy.md",
                similarity_score=0.8,
                excerpt="MFA is required.",
            )
        ],
    )
    response = ManagerResponse(
        query="What is the security policy?",
        classification="QUALITATIVE",
        answers=[AgentAnswer(agent="qualitative", qualitative=qualitative)],
        final_answer="MFA is required.",
    )
    output = format_response(response)
    assert "MFA is required." in output
    assert "security_policy::chunk_0" in output
    assert "similarity=0.8" in output


def test_format_response_shows_sql_table():
    quantitative = QuantitativeResult(
        sql="SELECT region, total FROM revenue",
        columns=["region", "total"],
        rows=[["North America", 100]],
        summary="North America leads.",
    )
    response = ManagerResponse(
        query="Show revenue by region",
        classification="QUANTITATIVE",
        answers=[AgentAnswer(agent="quantitative", quantitative=quantitative)],
        final_answer="North America leads.",
    )
    output = format_response(response)
    assert "SELECT region, total FROM revenue" in output
    assert "North America" in output
    assert "North America leads." in output


def test_format_response_combines_complex_answers():
    qualitative = QualitativeResult(answer="Policy answer.", citations=[])
    quantitative = QuantitativeResult(
        sql="SELECT 1", columns=["x"], rows=[[1]], summary="Data answer."
    )
    response = ManagerResponse(
        query="complex question",
        classification="COMPLEX",
        answers=[
            AgentAnswer(agent="qualitative", qualitative=qualitative),
            AgentAnswer(agent="quantitative", quantitative=quantitative),
        ],
        final_answer="Policy answer.\n\nData answer.",
    )
    output = format_response(response)
    assert "Combined answer:" in output
    assert "Policy answer." in output
    assert "Data answer." in output
