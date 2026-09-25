import argparse
import sys

from tabulate import tabulate

from multiagent.factory import build_manager_agent
from multiagent.logging_config import configure_logging


def format_response(response):
    lines = [
        "",
        f"Query: {response.query}",
        f"Classification: {response.classification}",
        "-" * 60,
    ]

    if response.clarification_question:
        lines.append(response.clarification_question)
        return "\n".join(lines)

    for answer in response.answers:
        if answer.agent == "qualitative" and answer.qualitative:
            lines.append(f"[Qualitative Agent]\n{answer.qualitative.answer}")
            if answer.qualitative.citations:
                lines.append("\nSources:")
                for citation in answer.qualitative.citations:
                    lines.append(
                        f"  - {citation.document_id} ({citation.source}), "
                        f"similarity={citation.similarity_score}"
                    )
            lines.append("")
        elif answer.agent == "quantitative" and answer.quantitative:
            lines.append(f"[Quantitative Agent]\nSQL: {answer.quantitative.sql}")
            if answer.quantitative.rows:
                table = tabulate(
                    answer.quantitative.rows[:15],
                    headers=answer.quantitative.columns,
                    tablefmt="simple",
                )
                lines.append(table)
            lines.append(f"\n{answer.quantitative.summary}")
            lines.append("")

    if len(response.answers) > 1:
        lines.append("-" * 60)
        lines.append("Combined answer:")
        lines.append(response.final_answer)

    return "\n".join(lines)


def run_query(manager, query):
    response = manager.handle(query)
    print(format_response(response))


def interactive_loop(manager):
    print("Multi-Agent RAG System for Enterprise Documentation")
    print("Type a question, or 'exit' to quit.\n")
    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        run_query(manager, query)


def main():
    parser = argparse.ArgumentParser(
        description="Multi-agent RAG system for enterprise documentation"
    )
    parser.add_argument(
        "query", nargs="?", help="Query to run. Omit to start interactive mode."
    )
    args = parser.parse_args()

    configure_logging()
    manager = build_manager_agent()

    if args.query:
        run_query(manager, args.query)
    else:
        interactive_loop(manager)


if __name__ == "__main__":
    sys.exit(main())
