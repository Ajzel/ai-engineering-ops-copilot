
import pytest

from ops_copilot.agent import (
    get_provider_configs,
    is_retryable_provider_error,
)


def test_provider_order_and_configuration(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("OPENROUTER_API_KEY_1", "test-deepseek")
    monkeypatch.setenv("OPENROUTER_API_KEY_2", "test-glm")

    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv(
        "OPENROUTER_MODEL_1",
        "deepseek/deepseek-v4.1-flash",
    )
    monkeypatch.setenv(
        "OPENROUTER_MODEL_2",
        "z-ai/glm-5.3-flash",
    )

    providers = get_provider_configs()

    assert [p["name"] for p in providers] == [
        "Groq",
        "OpenRouter-DeepSeek",
        "OpenRouter-GLM",
    ]

    assert providers[0]["model"] == "openai/gpt-oss-120b"
    assert providers[1]["model"] == "deepseek/deepseek-v4.1-flash"
    assert providers[2]["model"] == "z-ai/glm-5.3-flash"


def test_no_providers_configured(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY_1", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY_2", raising=False)

    assert get_provider_configs() == []


@pytest.mark.parametrize(
    "error",
    [
        "429 Too Many Requests",
        "402 Payment Required"
        "insufficient credits",
        "rate_limit exceeded",
        "500 Internal Server Error",
        "502 Bad Gateway",
        "503 Service Unavailable",
        "504 Gateway Timeout",
        "Connection error",
        "Connection reset",
        "Request timed out",
    ],
)
def test_retryable_provider_errors(error):
    assert is_retryable_provider_error(Exception(error)) is True


@pytest.mark.parametrize(
    "error",
    [
        "Tool call validation failed",
        "invalid_tool_call",
        "tool_use_failed",
        "413 Request Entity Too Large",
        "context_length_exceeded",
        "request_too_large",
        "400 Bad Request",
    ],
)
def test_non_retryable_provider_errors(error):
    assert is_retryable_provider_error(Exception(error)) is False


def test_unknown_error_is_not_retryable():
    assert is_retryable_provider_error(
        Exception("Unexpected application error")
    ) is False


from unittest.mock import AsyncMock, Mock

import ops_copilot.agent as agent_module


@pytest.fixture
def mock_providers():
    return [
        {
            "name": "Groq",
            "model": "openai/gpt-oss-120b",
            "create_llm": Mock(return_value="groq-llm"),
        },
        {
            "name": "OpenRouter-DeepSeek",
            "model": "deepseek/deepseek-v4.1-flash",
            "create_llm": Mock(return_value="deepseek-llm"),
        },
        {
            "name": "OpenRouter-GLM",
            "model": "z-ai/glm-5.3-flash",
            "create_llm": Mock(return_value="glm-llm"),
        },
    ]

@pytest.mark.asyncio
async def test_groq_failure_falls_back_to_deepseek(mock_providers):
    agents = []
    outcomes = iter([
        Exception("503 Service Unavailable"),
        "Investigation completed",
    ])

    def agent_factory(**kwargs):
        mock_agent = Mock()
        outcome = next(outcomes)

        if isinstance(outcome, Exception):
            mock_agent.run = AsyncMock(side_effect=outcome)
        else:
            mock_agent.run = AsyncMock(return_value=outcome)

        agents.append(mock_agent)
        return mock_agent

    response, provider = await agent_module.execute_with_provider_fallback(
        question="Investigate INC-002",
        providers=mock_providers,
        client=Mock(),
        agent_factory=agent_factory,
    )

    assert response == "Investigation completed"
    assert provider == "OpenRouter-DeepSeek"
    assert len(agents) == 2
    assert mock_providers[2]["create_llm"].call_count == 0

@pytest.mark.asyncio
async def test_fallback_reaches_glm(mock_providers):
    outcomes = iter([
        Exception("429 Rate limit exceeded"),
        Exception("502 Bad Gateway"),
        "GLM investigation completed",
    ])

    def agent_factory(**kwargs):
        mock_agent = Mock()
        outcome = next(outcomes)

        if isinstance(outcome, Exception):
            mock_agent.run = AsyncMock(side_effect=outcome)
        else:
            mock_agent.run = AsyncMock(return_value=outcome)

        return mock_agent

    response, provider = await agent_module.execute_with_provider_fallback(
        question="Investigate INC-002",
        providers=mock_providers,
        client=Mock(),
        agent_factory=agent_factory,
    )

    assert response == "GLM investigation completed"
    assert provider == "OpenRouter-GLM"

@pytest.mark.asyncio
async def test_all_providers_fail(mock_providers):
    def agent_factory(**kwargs):
        mock_agent = Mock()
        mock_agent.run = AsyncMock(
            side_effect=Exception("503 Service Unavailable")
        )
        return mock_agent

    with pytest.raises(
        RuntimeError,
        match="All configured AI providers failed",
    ):
        await agent_module.execute_with_provider_fallback(
            question="Investigate INC-002",
            providers=mock_providers,
            client=Mock(),
            agent_factory=agent_factory,
        )


@pytest.mark.asyncio
async def test_non_retryable_error_stops_fallback(mock_providers):
    def agent_factory(**kwargs):
        mock_agent = Mock()
        mock_agent.run = AsyncMock(
            side_effect=Exception("400 Bad Request")
        )
        return mock_agent

    with pytest.raises(Exception, match="400 Bad Request"):
        await agent_module.execute_with_provider_fallback(
            question="Investigate INC-002",
            providers=mock_providers,
            client=Mock(),
            agent_factory=agent_factory,
        )

    assert mock_providers[0]["create_llm"].call_count == 1
    assert mock_providers[1]["create_llm"].call_count == 0
    assert mock_providers[2]["create_llm"].call_count == 0


@pytest.mark.asyncio
async def test_memory_enabled_for_every_provider_attempt(mock_providers):
    agent_configs = []

    outcomes = iter([
        Exception("503 Service Unavailable"),
        "DeepSeek succeeded",
    ])

    def agent_factory(**kwargs):
        agent_configs.append(kwargs)

        mock_agent = Mock()
        outcome = next(outcomes)

        if isinstance(outcome, Exception):
            mock_agent.run = AsyncMock(side_effect=outcome)
        else:
            mock_agent.run = AsyncMock(return_value=outcome)

        return mock_agent

    await agent_module.execute_with_provider_fallback(
        question="Investigate INC-002",
        providers=mock_providers,
        client=Mock(),
        agent_factory=agent_factory,
    )

    assert len(agent_configs) == 2

    for config in agent_configs:
        assert config["memory_enabled"] is True
        assert config["retry_on_error"] is False
        assert config["system_prompt"] == agent_module.INVESTIGATION_POLICY
        
@pytest.mark.asyncio
async def test_402_error_falls_back_to_glm(mock_providers):
    agents = []

    outcomes = iter([
        Exception("429 Too Many Requests"),
        Exception("402 Payment Required: insufficient credits"),
        "GLM investigation completed successfully",
    ])

    def agent_factory(**kwargs):
        mock_agent = Mock()
        outcome = next(outcomes)

        if isinstance(outcome, Exception):
            mock_agent.run = AsyncMock(side_effect=outcome)
        else:
            mock_agent.run = AsyncMock(return_value=outcome)

        agents.append(mock_agent)
        return mock_agent

    response, provider = await agent_module.execute_with_provider_fallback(
        question="Investigate INC-002",
        providers=mock_providers,
        client=Mock(),
        agent_factory=agent_factory,
    )

    assert response == "GLM investigation completed successfully"
    assert provider == "OpenRouter-GLM"
    assert len(agents) == 3

    for provider_config in mock_providers:
        assert provider_config["create_llm"].call_count == 1