from typing import Optional

from pydantic import BaseModel


class Citation(BaseModel):
    document_id: str
    source: str
    similarity_score: float
    excerpt: str


class QualitativeResult(BaseModel):
    answer: str
    citations: list[Citation]
    below_threshold: bool = False


class QuantitativeResult(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list]
    summary: str


class AgentAnswer(BaseModel):
    agent: str
    qualitative: Optional[QualitativeResult] = None
    quantitative: Optional[QuantitativeResult] = None
    error: Optional[str] = None


class ManagerResponse(BaseModel):
    query: str
    classification: str
    answers: list[AgentAnswer] = []
    final_answer: str = ""
    clarification_question: Optional[str] = None


class QueryRequest(BaseModel):
    query: str
