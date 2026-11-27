
import pytest

from ops_copilot.data_sources.base import SyntheticDataSource
from ops_copilot.data_sources.factory import create_data_source


def test_factory_defaults_to_synthetic(monkeypatch):
    monkeypatch.delenv("OPS_COPILOT_DATA_SOURCE", raising=False)

    source = create_data_source()

    assert isinstance(source, SyntheticDataSource)


def test_factory_accepts_explicit_synthetic(monkeypatch):
    monkeypatch.setenv("OPS_COPILOT_DATA_SOURCE", "synthetic")

    source = create_data_source()

    assert isinstance(source, SyntheticDataSource)


def test_factory_rejects_unsupported_provider(monkeypatch):
    monkeypatch.setenv("OPS_COPILOT_DATA_SOURCE", "prometheus")

    with pytest.raises(ValueError, match="Unsupported data source"):
        create_data_source()
