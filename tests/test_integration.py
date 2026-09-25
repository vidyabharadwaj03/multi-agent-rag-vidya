from multiagent.manager_agent import ManagerAgent
from multiagent.qualitative_agent import QualitativeAgent
from multiagent.quantitative_agent import QuantitativeAgent
from multiagent.vector_store import VectorStore
from tests.fakes import FakeLLMClient


def build_manager(tmp_path, test_db, classify_response, extra_responses, docs=None):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    docs = docs or {
        "security.md": (
            "# Security Policy\n\nAll employees must use multi-factor authentication."
        )
    }
    for filename, content in docs.items():
        (docs_dir / filename).write_text(content)

    vector_store = VectorStore(str(tmp_path / "chroma"))
    vector_store.ingest_directory(str(docs_dir))

    llm_client = FakeLLMClient(responses=[classify_response] + extra_responses)

    qualitative_agent = QualitativeAgent(vector_store, llm_client, relevance_threshold=0.3)
    quantitative_agent = QuantitativeAgent(test_db, llm_client)

    return ManagerAgent(qualitative_agent, quantitative_agent, llm_client)


def test_end_to_end_qualitative_query(tmp_path, test_db):
    manager = build_manager(
        tmp_path,
        test_db,
        classify_response="QUALITATIVE",
        extra_responses=["MFA is required for all employees."],
    )

    response = manager.handle("What is our security policy on authentication?")

    assert response.classification == "QUALITATIVE"
    assert "MFA" in response.final_answer
    assert response.answers[0].qualitative.citations


def test_end_to_end_quantitative_query(tmp_path, test_db):
    manager = build_manager(
        tmp_path,
        test_db,
        classify_response="QUANTITATIVE",
        extra_responses=[
            "SELECT region, SUM(amount) as total FROM revenue GROUP BY region",
            "North America has the highest total revenue.",
        ],
    )

    response = manager.handle("Show me revenue by region")

    assert response.classification == "QUANTITATIVE"
    quantitative_result = response.answers[0].quantitative
    assert len(quantitative_result.rows) == 4
    assert "North America" in response.final_answer


def test_end_to_end_complex_query(tmp_path, test_db):
    docs = {
        "employee_handbook.md": (
            "# Employee Satisfaction\n\n"
            "The company runs a quarterly employee satisfaction survey. "
            "Remote work policy allows flexible schedules to improve satisfaction."
        )
    }
    manager = build_manager(
        tmp_path,
        test_db,
        classify_response="COMPLEX",
        extra_responses=[
            "Remote work policy improves employee satisfaction.",
            "SELECT AVG(score) as avg_score FROM employee_satisfaction",
            "Average employee satisfaction is moderate.",
        ],
        docs=docs,
    )

    response = manager.handle(
        "How does our employee satisfaction compare and what policies impact this?"
    )

    assert response.classification == "COMPLEX"
    assert len(response.answers) == 2
    assert "Remote work policy" in response.final_answer
    assert "Average employee satisfaction" in response.final_answer
