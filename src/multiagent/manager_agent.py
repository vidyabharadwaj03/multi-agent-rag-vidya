from multiagent.logging_config import Timer, get_logger, log_event
from multiagent.schemas import AgentAnswer, ManagerResponse

VALID_LABELS = {"QUALITATIVE", "QUANTITATIVE", "COMPLEX", "AMBIGUOUS"}

QUANTITATIVE_KEYWORDS = [
    "revenue", "sales", "churn", "rate", "trend", "compare", "how many",
    "how much", "percentage", "total", "average", "growth", "performance",
    "quarter", "q1", "q2", "q3", "q4",
]
QUALITATIVE_KEYWORDS = [
    "policy", "process", "explain", "how do we", "procedure", "handbook",
    "strategy", "guideline",
]


class ManagerAgent:
    def __init__(self, qualitative_agent, quantitative_agent, llm_client):
        self.qualitative_agent = qualitative_agent
        self.quantitative_agent = quantitative_agent
        self.llm_client = llm_client
        self.logger = get_logger("manager_agent")

    def classify(self, query):
        prompt = (
            "Classify the following user query into exactly one category:\n"
            "QUALITATIVE - questions about policies, processes, or documentation\n"
            "QUANTITATIVE - questions about data, metrics, revenue, sales, or numbers\n"
            "COMPLEX - questions that need both document knowledge and data analysis\n"
            "AMBIGUOUS - questions that are unclear or too vague to route confidently\n\n"
            f"Query: {query}\n\n"
            "Respond with only one word: QUALITATIVE, QUANTITATIVE, COMPLEX, or AMBIGUOUS."
        )
        try:
            raw = self.llm_client.complete(
                prompt, system="You are a query router.", max_tokens=800
            )
            label = raw.strip().upper().split()[0].strip(".")
        except Exception:
            label = ""

        if label not in VALID_LABELS:
            label = self._fallback_classify(query)
        return label

    def _fallback_classify(self, query):
        lower = query.lower()
        has_quant = any(keyword in lower for keyword in QUANTITATIVE_KEYWORDS)
        has_qual = any(keyword in lower for keyword in QUALITATIVE_KEYWORDS)
        if has_quant and has_qual:
            return "COMPLEX"
        if has_quant:
            return "QUANTITATIVE"
        if has_qual:
            return "QUALITATIVE"
        return "AMBIGUOUS"

    def _generate_clarification(self, query):
        prompt = (
            f"A user asked: \"{query}\"\n\n"
            "This question is too ambiguous to route to a documentation search or a "
            "data query. Ask a single, short clarifying question to help figure out "
            "what they need."
        )
        try:
            return self.llm_client.complete(prompt, max_tokens=800)
        except Exception:
            return (
                "Could you clarify whether you're asking about a policy or process "
                "(qualitative) or about data or metrics (quantitative)?"
            )

    def handle(self, query):
        answers = []
        clarification = None

        with Timer() as timer:
            classification = self.classify(query)

            if classification == "AMBIGUOUS":
                clarification = self._generate_clarification(query)
                final_answer = clarification
            else:
                if classification in ("QUALITATIVE", "COMPLEX"):
                    qualitative_result = self.qualitative_agent.answer(query)
                    answers.append(
                        AgentAnswer(agent="qualitative", qualitative=qualitative_result)
                    )
                if classification in ("QUANTITATIVE", "COMPLEX"):
                    quantitative_result = self.quantitative_agent.answer(query)
                    answers.append(
                        AgentAnswer(agent="quantitative", quantitative=quantitative_result)
                    )
                final_answer = self._compose_final_answer(classification, answers)

        log_event(
            self.logger,
            "query_routed",
            query=query,
            classification=classification,
            agents_used=[a.agent for a in answers],
            execution_time_seconds=round(timer.elapsed_seconds, 4),
        )

        return ManagerResponse(
            query=query,
            classification=classification,
            answers=answers,
            final_answer=final_answer,
            clarification_question=clarification,
        )

    def _compose_final_answer(self, classification, answers):
        if classification == "COMPLEX":
            parts = []
            for answer in answers:
                if answer.agent == "qualitative":
                    parts.append(
                        f"[Qualitative Agent handled the policy/process part]\n"
                        f"{answer.qualitative.answer}"
                    )
                elif answer.agent == "quantitative":
                    parts.append(
                        f"[Quantitative Agent handled the data/metrics part]\n"
                        f"{answer.quantitative.summary}"
                    )
            return "\n\n".join(parts)

        answer = answers[0]
        if answer.agent == "qualitative":
            return answer.qualitative.answer
        return answer.quantitative.summary
