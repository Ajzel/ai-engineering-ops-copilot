
from ops_copilot.data_sources.base import SyntheticDataSource
from ops_copilot.data_sources import synthetic


def test_synthetic_data_source_returns_existing_datasets():
    source = SyntheticDataSource()

    assert source.get_incidents() is synthetic.INCIDENTS
    assert source.get_logs() is synthetic.LOGS
    assert source.get_service_metrics() is synthetic.SERVICE_METRICS
    assert source.get_traces() is synthetic.TRACES
    assert source.get_deployments() is synthetic.DEPLOYMENTS


def test_synthetic_data_source_record_counts():
    source = SyntheticDataSource()

    assert len(source.get_incidents()) == 3
    assert len(source.get_logs()) == 5
    assert len(source.get_service_metrics()) == 3
    assert len(source.get_traces()) == 3
    assert len(source.get_deployments()) == 4
