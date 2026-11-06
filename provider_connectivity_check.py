
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

providers = [
    {
        "name": "Groq - GPT-OSS 120B",
        "key": os.getenv("GROQ_API_KEY"),
        "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        "type": "groq",
    },
    {
        "name": "OpenRouter - DeepSeek",
        "key": os.getenv("OPENROUTER_API_KEY_1"),
        "model": os.getenv(
            "OPENROUTER_MODEL_1",
            "deepseek/deepseek-v4.1-flash",
        ),
        "type": "openrouter",
    },
    {
        "name": "OpenRouter - GLM",
        "key": os.getenv("OPENROUTER_API_KEY_2"),
        "model": os.getenv(
            "OPENROUTER_MODEL_2",
            "z-ai/glm-5.3-flash",
        ),
        "type": "openrouter",
    },
]


def test_provider(provider):
    print("\n" + "=" * 55)
    print(f"TESTING: {provider['name']}")
    print(f"MODEL: {provider['model']}")

    if not provider["key"]:
        print("STATUS: SKIPPED - API key missing")
        return

    try:
        if provider["type"] == "groq":
            llm = ChatGroq(
                model=provider["model"],
                api_key=provider["key"],
                temperature=0,
                max_retries=0,
            )
        else:
            llm = ChatOpenAI(
                model=provider["model"],
                api_key=provider["key"],
                base_url="https://openrouter.ai/api/v1",
                temperature=0,
                max_retries=0,
                timeout=30,
            )

        response = llm.invoke(
            "Reply with exactly: PROVIDER_OK"
        )

        print("STATUS: SUCCESS")
        print("RESPONSE:", response.content)

    except Exception as exc:
        print("STATUS: FAILED")
        print("ERROR:", type(exc).__name__)
        print("DETAILS:", str(exc)[:1200])


if __name__ == "__main__":
    print("AI ENGINEERING OPS COPILOT")
    print("THREE-PROVIDER CONNECTIVITY TEST")

    for provider in providers:
        test_provider(provider)

    print("\n" + "=" * 55)
    print("ALL PROVIDER TESTS COMPLETED")
