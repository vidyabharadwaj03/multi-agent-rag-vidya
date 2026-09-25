from multiagent.config import get_settings
from multiagent.llm_client import LLMClient
from multiagent.manager_agent import ManagerAgent
from multiagent.qualitative_agent import QualitativeAgent
from multiagent.quantitative_agent import QuantitativeAgent
from multiagent.vector_store import VectorStore


def build_manager_agent(settings=None):
    settings = settings or get_settings()

    llm_client = LLMClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        base_url=settings.gemini_base_url,
    )
    vector_store = VectorStore(settings.chroma_persist_dir)

    qualitative_agent = QualitativeAgent(
        vector_store=vector_store,
        llm_client=llm_client,
        relevance_threshold=settings.relevance_threshold,
    )
    quantitative_agent = QuantitativeAgent(
        db_path=settings.sql_database_path, llm_client=llm_client
    )

    return ManagerAgent(
        qualitative_agent=qualitative_agent,
        quantitative_agent=quantitative_agent,
        llm_client=llm_client,
    )
