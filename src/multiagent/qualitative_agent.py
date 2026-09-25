from multiagent.logging_config import Timer, get_logger, log_event
from multiagent.schemas import Citation, QualitativeResult

NO_ANSWER_MESSAGE = (
    "I could not find relevant information in the enterprise documentation "
    "to answer this question."
)


class QualitativeAgent:
    def __init__(self, vector_store, llm_client, relevance_threshold):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.relevance_threshold = relevance_threshold
        self.logger = get_logger("qualitative_agent")

    def answer(self, query, k=4):
        with Timer() as timer:
            matches = self.vector_store.query(query, k=k)
        relevant = [
            m for m in matches if m["similarity_score"] >= self.relevance_threshold
        ]

        log_event(
            self.logger,
            "retrieval_complete",
            query=query,
            retrieved=len(matches),
            relevant=len(relevant),
            sources=[m["document_id"] for m in relevant],
            execution_time_seconds=round(timer.elapsed_seconds, 4),
        )

        if not relevant:
            return QualitativeResult(
                answer=NO_ANSWER_MESSAGE, citations=[], below_threshold=True
            )

        context = "\n\n".join(
            f"[{m['document_id']}] ({m['source']})\n{m['text']}" for m in relevant
        )
        prompt = (
            f"Context from enterprise documentation:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer the question using only the context above. Cite the document IDs "
            "you used in square brackets, for example [security_policy::chunk_0]. "
            "If the context does not contain the answer, say so explicitly."
        )
        answer_text = self.llm_client.complete(
            prompt,
            system=(
                "You are an enterprise documentation assistant. "
                "Only answer from the provided context."
            ),
        )

        citations = [
            Citation(
                document_id=m["document_id"],
                source=m["source"],
                similarity_score=round(m["similarity_score"], 4),
                excerpt=m["text"][:200],
            )
            for m in relevant
        ]
        return QualitativeResult(answer=answer_text, citations=citations)
