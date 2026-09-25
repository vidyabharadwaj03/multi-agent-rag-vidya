from fastapi.testclient import TestClient

from multiagent.api import app, get_manager
from multiagent.schemas import (
    AgentAnswer,
    ManagerResponse,
    QualitativeResult,
    QuantitativeResult,
)


class FakeManager:
    class qualitative_agent:
        @staticmethod
        def answer(query):
            return QualitativeResult(answer="fake qualitative answer", citations=[])

    class quantitative_agent:
        @staticmethod
        def answer(query):
            return QuantitativeResult(
                sql="SELECT 1", columns=["x"], rows=[[1]], summary="fake summary"
            )

    def handle(self, query):
        return ManagerResponse(
            query=query,
            classification="QUALITATIVE",
            answers=[
                AgentAnswer(
                    agent="qualitative",
                    qualitative=QualitativeResult(answer="fake answer", citations=[]),
                )
            ],
            final_answer="fake answer",
        )


def get_client():
    app.dependency_overrides[get_manager] = lambda: FakeManager()
    return TestClient(app)


def test_health_endpoint():
    client = get_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_endpoint():
    client = get_client()
    response = client.post("/query", json={"query": "What is our security policy?"})
    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == "QUALITATIVE"
    assert body["final_answer"] == "fake answer"


def test_qualitative_endpoint():
    client = get_client()
    response = client.post(
        "/qualitative/query", json={"query": "Explain the code review process"}
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "fake qualitative answer"


def test_quantitative_endpoint():
    client = get_client()
    response = client.post(
        "/quantitative/query", json={"query": "Show me monthly revenue"}
    )
    assert response.status_code == 200
    assert response.json()["sql"] == "SELECT 1"


def test_openapi_schema_is_available():
    client = get_client()
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/query" in response.json()["paths"]
