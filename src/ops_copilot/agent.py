
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


INVESTIGATION_POLICY = """
Investigate the user's request using the available MCP tools.

Evidence requirements:
1. Retrieve relevant incident details, logs, or other available evidence
   before drawing conclusions.
2. Treat tool results as the source of truth. Never invent logs, timestamps,
   metrics, configuration values, incident records, or service behavior.
3. Clearly separate observed facts, unconfirmed hypotheses, and unknowns.
4. Do not claim causation or event ordering unless the available evidence
   explicitly supports it.
5. Never report a root cause as confirmed without sufficient evidence.
6. If a tool returns an error or no matching records, report that limitation
   accurately. Never substitute a different incident for a missing one.
7. When an incident is not found, state that it was not found. Do not speculate
   that it was deleted, archived, incorrectly entered, or not yet indexed
   unless evidence explicitly supports that explanation.
8. Recommend diagnostic steps that could help verify hypotheses, but clearly
   identify them as proposed actions rather than completed investigations.
9. Recommend only actions and capabilities supported by the available tools.
   Do not assume that archives, audit logs, time-window filters, metrics,
   traces, deployment records, or other integrations are available unless
   the connected tools explicitly provide them.
10. Keep incident IDs, service names, severity, status, and log details
    consistent with retrieved evidence.
11. If evidence is insufficient, explain exactly what is missing and what
    additional evidence would help establish a conclusion.
12. Do not present a correlation, co-occurrence, or plausible explanation
    as proof of causation.
13. Do not claim to have executed a diagnostic, queried a system, or verified
    a hypothesis unless the corresponding tool result confirms that action.
14. Prefer concise, evidence-based answers over speculative explanations.
    If no supported hypothesis can be established, state that explicitly.

Trace analysis requirements:
15. Treat trace spans as recorded observations, not proof of causation.
16. Never infer causal relationships from span ordering alone.
17. Do not assume that one span caused another span to fail merely because
    it appears earlier in the trace.
18. Report each relevant span independently, including its span ID,
    service, operation, duration, status, and error when available.
19. Only establish causal relationships when explicit supporting evidence
    is available.
20. Clearly identify simulated or synthetic trace data whenever the tool
    marks it as simulated.
21. Do not describe simulated traces as production telemetry or real
    operational observations.
22. Do not recommend configuration changes, infrastructure modifications,
    or other remediation as necessary solutions without supporting evidence.
23. When trace information is incomplete, explicitly identify missing
    information rather than filling gaps with assumptions.

Tool capability and data-source constraints:
24. Distinguish simulated metrics from real-time production metrics.
25. Never describe synthetic development metrics as live monitoring data.
26. Before recommending a tool, verify that the requested capability
    is actually supported by that tool.
27. Do not imply that a tool supports time-window filtering,
    historical configuration lookup, deployment inspection,
    database health checks, or successful trace comparison
    unless its implementation explicitly provides that capability.
28. Clearly distinguish between:
    - Actions executable through available MCP tools.
    - Proposed manual investigation steps.
    - Future capabilities not currently implemented.
29. Do not claim that simulated evidence establishes actual
    production system behavior.

Response structure:
- Incident overview
- Observed facts and evidence
- Possible hypotheses, clearly labeled as unconfirmed
- What remains unconfirmed
- Recommended next diagnostic steps

For trace-specific requests:
- Trace overview
- Data source (clearly state whether simulated or real)
- Span-by-span observations
- Related incident information, if retrieved
- What the trace establishes
- What remains unconfirmed
- Recommended next diagnostic steps

For requests involving an incident that cannot be found, use a concise
response containing:
- Lookup result
- Evidence returned by the tool
- Investigation limitations
- Next step, if appropriate

Never fabricate evidence to make the report more complete.
"""




def build_investigation_prompt(question: str) -> str:
    """Build a consistent, evidence-grounded investigation prompt."""
    question = question.strip()

    if not question:
        raise ValueError("The investigation question cannot be empty.")

    return f"User investigation request:\n{question}\n\n{INVESTIGATION_POLICY}"


def create_mcp_config() -> dict:
    """Configure the local MCP server using the project virtual environment."""
    python_executable = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    server_path = PROJECT_ROOT / "src" / "ops_copilot" / "server.py"

    if not python_executable.is_file():
        raise FileNotFoundError(
            f"Project Python interpreter not found: {python_executable}"
        )

    if not server_path.is_file():
        raise FileNotFoundError(f"MCP server file not found: {server_path}")

    return {
        "mcpServers": {
            "ops-copilot": {
                "command": str(python_executable),
                "args": [str(server_path)],
            }
        }
    }


async def run_agent():
    """Run the AI Engineering Operations Copilot."""
    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    if not api_key or api_key == "your_actual_groq_api_key":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Configure it in the project .env file."
        )

    client = MCPClient.from_dict(create_mcp_config())

    try:
        llm = ChatGroq(
            model=model_name,
            api_key=api_key,
            temperature=0,
        )

        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=10,
            memory_enabled=True,
        )

        print("\nAI Engineering Operations Copilot")
        print(f"Model: {model_name}")
        print("Ask about incidents and logs. Type 'exit' to quit.\n")

        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting copilot.")
                break

            if question.lower() in {"exit", "quit"}:
                break

            if not question:
                print("Please enter an investigation question.")
                continue

            try:
                prompt = build_investigation_prompt(question)
                response = await agent.run(prompt)
                print(f"\nCopilot: {response}\n")

            except Exception as exc:
                # Log the error for debugging; keep the interactive session alive.
                logger.exception("Investigation request failed")
                print(
                    "\nThe investigation failed. Check the terminal logs "
                    "for details. You can try again or enter 'exit'.\n"
                )

    finally:
        try:
            await client.close_all_sessions()
        except Exception:
            logger.exception("Failed to close MCP sessions cleanly")


if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except (RuntimeError, FileNotFoundError) as exc:
        logger.error("%s", exc)
    except KeyboardInterrupt:
        print("\nCopilot stopped.")
