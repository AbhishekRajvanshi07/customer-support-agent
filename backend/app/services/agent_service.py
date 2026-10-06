"""
Defines the support Crew: a Knowledge Retriever agent and a Support
Specialist agent working together on each incoming customer message.

Why two agents instead of one RAG call? Separating "find the facts"
from "write the answer" keeps the retrieval step auditable (we can
log/inspect exactly what was retrieved) and lets the specialist
focus its prompt purely on tone, accuracy and escalation judgement.
"""
import logging
import time

from crewai import Agent, Crew, Process, Task
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.services.retrieval_tool import KnowledgeBaseRetrievalTool, best_match_confidence

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=settings.gemini_temperature,
        convert_system_message_to_human=True,
    )


class SupportCrew:
    def __init__(self) -> None:
        self._llm = _build_llm()
        self._retrieval_tool = KnowledgeBaseRetrievalTool()

        self.retriever_agent = Agent(
            role="Knowledge Retriever",
            goal="Find the most relevant passages in the enterprise knowledge base for the customer's question",
            backstory=(
                "You are a meticulous research assistant for a customer support team. "
                "You never guess — you only surface what the knowledge base actually contains, "
                "and you clearly say when nothing relevant was found."
            ),
            tools=[self._retrieval_tool],
            llm=self._llm,
            verbose=False,
            allow_delegation=False,
        )

        self.support_agent = Agent(
            role="Support Specialist",
            goal="Write an accurate, concise, friendly answer to the customer using only retrieved facts",
            backstory=(
                "You are a senior customer support specialist at an enterprise software company. "
                "You answer strictly from the knowledge base context you're given. "
                "If the context doesn't fully answer the question, you say so honestly and "
                "recommend escalation to a human agent rather than inventing details."
            ),
            llm=self._llm,
            verbose=False,
            allow_delegation=False,
        )

    def _build_tasks(self, question: str) -> list[Task]:
        retrieve_task = Task(
            description=(
                f"Search the knowledge base for information relevant to this customer question:\n"
                f'"{question}"\n'
                "Return the raw passages you found, with their sources."
            ),
            expected_output="The relevant knowledge base passages with source names, or a clear NO_RESULTS note.",
            agent=self.retriever_agent,
        )

        answer_task = Task(
            description=(
                f'Customer question: "{question}"\n\n'
                "Using ONLY the knowledge base passages retrieved in the previous step, write a "
                "clear, friendly, and accurate answer. Rules:\n"
                "1. Do not state anything that isn't supported by the retrieved passages.\n"
                "2. If the passages don't fully answer the question, say what you don't have "
                "   information on and suggest the customer be connected with a human agent.\n"
                "3. Keep the answer under 150 words.\n"
                "4. End your response on a new line with 'ESCALATE: yes' or 'ESCALATE: no' "
                "   depending on whether a human should follow up."
            ),
            expected_output="A customer-ready answer followed by an ESCALATE: yes/no line.",
            agent=self.support_agent,
            context=[retrieve_task],
        )
        return [retrieve_task, answer_task]

    def handle(self, question: str) -> dict:
        start = time.perf_counter()
        tasks = self._build_tasks(question)
        crew = Crew(
            agents=[self.retriever_agent, self.support_agent],
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )
        raw_output = str(crew.kickoff())
        latency_ms = int((time.perf_counter() - start) * 1000)

        answer, llm_escalate = _parse_escalation(raw_output)
        retrieval_confidence = best_match_confidence(question)

        # Escalate if EITHER the model asked for it OR the underlying
        # retrieval was weak — the API layer, not just the LLM, guards this.
        escalate = llm_escalate or retrieval_confidence < settings.escalation_confidence_threshold

        return {
            "answer": answer,
            "confidence": round(retrieval_confidence, 3),
            "escalate": escalate,
            "latency_ms": latency_ms,
        }


def _parse_escalation(raw_output: str) -> tuple[str, bool]:
    lines = raw_output.strip().splitlines()
    escalate = False
    answer_lines = []
    for line in lines:
        if line.strip().upper().startswith("ESCALATE:"):
            escalate = "yes" in line.strip().lower()
        else:
            answer_lines.append(line)
    return "\n".join(answer_lines).strip(), escalate


support_crew = SupportCrew()
