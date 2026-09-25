from multiagent.qualitative_agent import NO_ANSWER_MESSAGE, QualitativeAgent
from tests.fakes import FakeLLMClient


class FakeVectorStore:
    def __init__(self, matches):
        self.matches = matches
        self.queries = []

    def query(self, query_text, k=4):
        self.queries.append(query_text)
        return self.matches


def make_match(document_id, source, text, score):
    return {
        "document_id": document_id,
        "source": source,
        "text": text,
        "similarity_score": score,
    }


def test_answer_with_relevant_matches_returns_citations():
    matches = [
        make_match("security_policy::chunk_0", "security_policy.md", "MFA is required.", 0.8),
        make_match("security_policy::chunk_1", "security_policy.md", "Passwords must be long.", 0.5),
    ]
    vector_store = FakeVectorStore(matches)
    llm_client = FakeLLMClient(responses=["MFA is required for all employees. [security_policy::chunk_0]"])

    agent = QualitativeAgent(vector_store, llm_client, relevance_threshold=0.3)
    result = agent.answer("What is the security policy?")

    assert result.below_threshold is False
    assert len(result.citations) == 2
    assert result.citations[0].document_id == "security_policy::chunk_0"
    assert "MFA" in result.answer
    assert len(llm_client.calls) == 1


def test_answer_below_threshold_returns_no_answer_without_llm_call():
    matches = [make_match("random::chunk_0", "random.md", "irrelevant text", 0.05)]
    vector_store = FakeVectorStore(matches)
    llm_client = FakeLLMClient()

    agent = QualitativeAgent(vector_store, llm_client, relevance_threshold=0.3)
    result = agent.answer("What is the meaning of life?")

    assert result.below_threshold is True
    assert result.answer == NO_ANSWER_MESSAGE
    assert result.citations == []
    assert len(llm_client.calls) == 0


def test_answer_filters_out_matches_below_threshold():
    matches = [
        make_match("a::chunk_0", "a.md", "relevant", 0.6),
        make_match("b::chunk_0", "b.md", "not relevant enough", 0.1),
    ]
    vector_store = FakeVectorStore(matches)
    llm_client = FakeLLMClient(responses=["answer"])

    agent = QualitativeAgent(vector_store, llm_client, relevance_threshold=0.3)
    result = agent.answer("some question")

    assert len(result.citations) == 1
    assert result.citations[0].document_id == "a::chunk_0"
