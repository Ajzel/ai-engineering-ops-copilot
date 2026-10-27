
import pytest

from ops_copilot.agent import build_investigation_prompt


def test_prompt_includes_user_question():
    prompt = build_investigation_prompt("Investigate INC-002")

    assert "Investigate INC-002" in prompt


def test_prompt_requires_evidence():
    prompt = build_investigation_prompt("Investigate INC-002")

    assert "Never invent logs" in prompt
    assert "Observed facts" in prompt
    assert "hypotheses" in prompt.lower()


def test_prompt_rejects_empty_question():
    with pytest.raises(ValueError, match="cannot be empty"):
        build_investigation_prompt("   ")


def test_prompt_requires_causation_evidence():
    prompt = build_investigation_prompt("Did error A cause error B?")

    assert "Do not claim causation" in prompt
    assert "without sufficient evidence" in prompt
