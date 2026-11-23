
import pytest

from ops_copilot.data_sources.config import get_data_source_mode


def test_default_data_source_is_synthetic(monkeypatch):
    monkeypatch.delenv("OPS_COPILOT_DATA_SOURCE", raising=False)

    assert get_data_source_mode() == "synthetic"


def test_explicit_synthetic_mode(monkeypatch):
    monkeypatch.setenv("OPS_COPILOT_DATA_SOURCE", "synthetic")

    assert get_data_source_mode() == "synthetic"


def test_unsupported_real_mode(monkeypatch):
    monkeypatch.setenv("OPS_COPILOT_DATA_SOURCE", "real")

    with pytest.raises(ValueError, match="Unsupported data source"):
        get_data_source_mode()
