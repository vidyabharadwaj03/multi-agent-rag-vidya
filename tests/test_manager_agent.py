from multiagent.manager_agent import ManagerAgent
from multiagent.schemas import QualitativeResult, QuantitativeResult
from tests.fakes import FakeLLMClient, RaisingLLMClient


class FakeQualitativeAgent:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def answer(self, query):
        self.calls.append(query)
        return self.result


class FakeQuantitativeAgent:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def answer(self, query):
        self.calls.append(query)
        return self.result


def make_qualitative_result():
    return QualitativeResult(answer="Here is the policy answer.", citations=[])


def make_quantitative_result():
    return QuantitativeResult(
        sql="SELECT 1", columns=["x"], rows=[[1]], summary="Here is the data answer."
    )


def test_qualitative_classification_routes_to_qualitative_only():
    qualitative_agent = FakeQualitativeAgent(make_qualitative_result())
    quantitative_agent = FakeQuantitativeAgent(make_quantitative_result())
    llm_client = FakeLLMClient(responses=["QUALITATIVE"])

    manager = ManagerAgent(qualitative_agent, quantitative_agent, llm_client)
    response = manager.handle("Explain the code review process")

    assert response.classification == "QUALITATIVE"
    assert len(response.answers) == 1
    assert response.answers[0].agent == "qualitative"
    assert response.final_answer == "Here is the policy answer."
    assert quantitative_agent.calls == []


def test_quantitative_classification_routes_to_quantitative_only():
    qualitative_agent = FakeQualitativeAgent(make_qualitative_result())
    quantitative_agent = FakeQuantitativeAgent(make_quantitative_result())
    llm_client = FakeLLMClient(responses=["QUANTITATIVE"])

    manager = ManagerAgent(qualitative_agent, quantitative_agent, llm_client)
    response = manager.handle("Show me monthly revenue trends")

    assert response.classification == "QUANTITATIVE"
    assert len(response.answers) == 1
    assert response.answers[0].agent == "quantitative"
    assert qualitative_agent.calls == []


def test_complex_classification_merges_both_agents():
    qualitative_agent = FakeQualitativeAgent(make_qualitative_result())
    quantitative_agent = FakeQuantitativeAgent(make_quantitative_result())
    llm_client = FakeLLMClient(responses=["COMPLEX"])

    manager = ManagerAgent(qualitative_agent, quantitative_agent, llm_client)
    response = manager.handle(
        "How does our employee satisfaction compare and what policies impact this?"
    )

    assert response.classification == "COMPLEX"
    assert len(response.answers) == 2
    assert "Here is the policy answer." in response.final_answer
    assert "Here is the data answer." in response.final_answer
    assert "Qualitative Agent" in response.final_answer
    assert "Quantitative Agent" in response.final_answer


def test_ambiguous_classification_returns_clarification_without_calling_agents():
    qualitative_agent = FakeQualitativeAgent(make_qualitative_result())
    quantitative_agent = FakeQuantitativeAgent(make_quantitative_result())
    llm_client = FakeLLMClient(responses=["AMBIGUOUS", "Could you clarify what you mean?"])

    manager = ManagerAgent(qualitative_agent, quantitative_agent, llm_client)
    response = manager.handle("tell me stuff")

    assert response.classification == "AMBIGUOUS"
    assert response.clarification_question == "Could you clarify what you mean?"
    assert response.answers == []
    assert qualitative_agent.calls == []
    assert quantitative_agent.calls == []


def test_classification_falls_back_to_keywords_when_llm_fails():
    qualitative_agent = FakeQualitativeAgent(make_qualitative_result())
    quantitative_agent = FakeQuantitativeAgent(make_quantitative_result())
    llm_client = RaisingLLMClient()

    manager = ManagerAgent(qualitative_agent, quantitative_agent, llm_client)
    response = manager.handle("Explain the code review process")

    assert response.classification == "QUALITATIVE"


def test_classification_falls_back_when_llm_returns_invalid_label():
    qualitative_agent = FakeQualitativeAgent(make_qualitative_result())
    quantitative_agent = FakeQuantitativeAgent(make_quantitative_result())
    llm_client = FakeLLMClient(responses=["I'm not sure how to classify this."])

    manager = ManagerAgent(qualitative_agent, quantitative_agent, llm_client)
    response = manager.handle("What is our churn rate?")

    assert response.classification == "QUANTITATIVE"
