
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_provider_configs() -> list[dict]:
    """Return configured providers in priority order."""

    providers = []

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        providers.append({
            "name": "Groq",
            "model": os.getenv(
                "GROQ_MODEL", "openai/gpt-oss-120b"
            ),
            "create_llm": lambda: ChatGroq(
                model=os.getenv(
                    "GROQ_MODEL", "openai/gpt-oss-120b"
                ),
                api_key=groq_key,
                temperature=0,
                max_retries=0,
            ),
        })

    openrouter_key_1 = os.getenv("OPENROUTER_API_KEY_1")
    if openrouter_key_1:
        providers.append({
            "name": "OpenRouter-DeepSeek",
            "model": os.getenv(
                "OPENROUTER_MODEL_1",
                "deepseek/deepseek-v4.1-flash",
            ),
            "create_llm": lambda: ChatOpenAI(
                model=os.getenv(
                    "OPENROUTER_MODEL_1",
                    "deepseek/deepseek-v4.1-flash",
                ),
                api_key=openrouter_key_1,
                base_url="https://openrouter.ai/api/v1",
                temperature=0,
                max_retries=0,
                timeout=60,
            ),
        })

    openrouter_key_2 = os.getenv("OPENROUTER_API_KEY_2")
    if openrouter_key_2:
        providers.append({
            "name": "OpenRouter-GLM",
            "model": os.getenv(
                "OPENROUTER_MODEL_2",
                "z-ai/glm-5.3-flash",
            ),
            "create_llm": lambda: ChatOpenAI(
                model=os.getenv(
                    "OPENROUTER_MODEL_2",
                    "z-ai/glm-5.3-flash",
                ),
                api_key=openrouter_key_2,
                base_url="https://openrouter.ai/api/v1",
                temperature=0,
                max_retries=0,
                timeout=60,
            ),
        })

    return providers


def is_retryable_provider_error(exc: Exception) -> bool:
    """Identify provider failures that justify trying another provider."""

    message = str(exc).lower()

    # Invalid tool calls and oversized requests are not
    # ordinary provider availability failures.
    non_retryable = [
        "tool call validation failed",
        "invalid_tool_call",
        "tool_use_failed",
        "413",
        "context_length_exceeded",
        "request_too_large",
    ]

    if any(term in message for term in non_retryable):
        return False

    retryable = [
        "429",
        "rate_limit",
        "rate limit",
        "500",
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "connection error",
        "connection reset",
        "service unavailable",
    ]

    return any(term in message for term in retryable)


async def execute_with_provider_fallback(
    question: str,
    providers: list[dict],
    client,
    agent_factory=None,
) -> tuple[str, str]:
    """Execute an investigation with sequential provider fallback."""

    factory = agent_factory or MCPAgent
    last_error = None

    for index, provider in enumerate(providers):
        provider_name = provider["name"]

        logger.info("Attempting provider: %s", provider_name)

        try:
            llm = provider["create_llm"]()

            agent = factory(
                llm=llm,
                client=client,
                max_steps=8,
                memory_enabled=True,
                system_prompt=INVESTIGATION_POLICY,
                retry_on_error=False,
            )

            # The investigation policy is already supplied as the
            # system prompt. Avoid appending it again to the question.
            response = await agent.run(question)

            logger.info("Provider succeeded: %s", provider_name)

            return response, provider_name

        except Exception as exc:
            last_error = exc

            logger.exception(
                "Provider %s failed",
                provider_name,
            )

            if not is_retryable_provider_error(exc):
                raise

            if index < len(providers) - 1:
                logger.warning(
                    "Retryable failure from %s. "
                    "Switching to the next provider.",
                    provider_name,
                )

    raise RuntimeError(
        "All configured AI providers failed."
    ) from last_error

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
    
Deployment investigation requirements:
30. Treat deployment records as evidence of recorded deployment
    events, not proof of incident causation.
31. Never infer that a deployment caused an incident solely
    because its timestamp or change description appears relevant.
32. Do not assume incident log timestamps are available.
    The current search_application_logs tool does not return timestamps.
33. Do not use static synthetic service metrics to establish
    historical trends or temporal relationships with deployments.
34. Do not claim that get_trace_details can capture new traces.
    It only retrieves existing trace records.
35. Do not recommend rollback, redeployment, or configuration
    changes as necessary actions without sufficient supporting
    evidence and operational validation.
36. Clearly distinguish deployment status from application health.
    A failed deployment does not automatically establish that
    the application is unhealthy.
    
Temporal correlation requirements:
37. Never infer an incident occurrence timestamp from its
    current status, including "open", "investigating", or "resolved".
38. Never describe deployments as occurring before or after
    an incident unless the incident timestamp is explicitly
    available.
39. Deployment timestamps alone cannot establish temporal
    proximity to an incident.
40. Do not claim that the correlation tool evaluates temporal
    proximity unless its actual implementation performs
    timestamp-based comparison using both incident and
    deployment timestamps.
41. Distinguish service matching and keyword overlap from
    temporal correlation.
42. Never recommend an unavailable MCP capability as an action
    the copilot can execute. Clearly label it as a manual investigation
    requiring an external system.

43. The current search_application_logs tool does not support
    timestamp-based filtering or return log timestamps.

44. The current get_service_metrics tool returns static synthetic
    values. It cannot retrieve historical metrics, connection-pool
    usage trends, or before-and-after deployment comparisons.

45. The current deployment tools return deployment metadata and
    change descriptions only. They do not retrieve configuration
    diffs, pipeline execution logs, rollback details, or
    post-deployment health-check results.

46. The current tools cannot independently check downstream
    database health, network conditions, or external infrastructure.
    Identify these as evidence gaps rather than claiming to have
    investigated them.
    
Recommendation constraints:
- Prioritize actions that can actually be performed with available MCP tools.
- Separate executable MCP actions from proposed external/manual actions.
- Do not repeatedly recommend unavailable capabilities as though
  they were implemented.
- If no further investigation can be performed with available tools,
  state that explicitly.
  
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
    """Run the copilot with automatic multi-provider fallback."""

    providers = get_provider_configs()

    if not providers:
        raise RuntimeError(
            "No AI providers configured. Check your .env file."
        )

    client = MCPClient.from_dict(create_mcp_config())

    try:
        print("\nAI Engineering Operations Copilot")
        print("Configured providers:")

        for index, provider in enumerate(providers, start=1):
            print(
                f"{index}. {provider['name']} "
                f"({provider['model']})"
            )

        print("\nAsk about incidents and logs. Type 'exit' to quit.\n")

        while True:
            try:
                question = input("You: ").strip()

            except (EOFError, KeyboardInterrupt):
                print("\nExiting copilot.")
                break

            if question.lower() in {"exit", "quit"}:
                print("\nExiting copilot.")
                break

            if not question:
                print("Please enter an investigation question.")
                continue

            try:
                print("\nStarting investigation...")

                response, provider_name = (
                    await execute_with_provider_fallback(
                        question=question,
                        providers=providers,
                        client=client,
                    )
                )

                print(f"\nProvider used: {provider_name}")
                print(f"\nCopilot: {response}\n")

            except Exception as exc:
                logger.exception("Investigation failed")

                print("\nInvestigation unsuccessful.")

                if isinstance(exc, RuntimeError):
                    print(f"Reason: {exc}")
                else:
                    print(
                        f"Error: {type(exc).__name__}: "
                        f"{str(exc)[:1000]}"
                    )

                print("Check the terminal logs for details.\n")

    finally:
        try:
            await client.close_all_sessions()

        except Exception:
            logger.exception(
                "Failed to close MCP sessions cleanly"
            )


if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except (RuntimeError, FileNotFoundError) as exc:
        logger.error("%s", exc)
    except KeyboardInterrupt:
        print("\nCopilot stopped.")
