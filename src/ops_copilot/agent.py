
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


async def run_agent():
    """Run the AI Engineering Operations Copilot."""

    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Configure it in your .env file."
        )

    model_name = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    mcp_config = {
        "mcpServers": {
            "ops-copilot": {
                "command": str(
                    PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
                ),
                "args": [
                    str(
                        PROJECT_ROOT
                        / "src"
                        / "ops_copilot"
                        / "server.py"
                    )
                ],
            }
        }
    }

    client = MCPClient.from_dict(mcp_config)

    llm = ChatGroq(
        model=model_name,
        api_key=groq_api_key,
        temperature=0,
    )

    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10,
        memory_enabled=True,
    )

    try:
        print("\nAI Engineering Operations Copilot")
        print("Ask about incidents and logs.")
        print("Type 'exit' to quit.\n")

        while True:
            question = input("You: ").strip()

            if question.lower() in {"exit", "quit"}:
                break

            if not question:
                continue

            try:
                response = await agent.run(
                    question
                    + "\nUse available MCP tools to gather evidence. "
                    "Separate observed facts from hypotheses. "
                    "Never claim a confirmed root cause without evidence."
                )

                print(f"\nCopilot: {response}\n")

            except Exception as exc:
                print(f"\nAgent error: {exc}\n")

    finally:
        await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(run_agent())
