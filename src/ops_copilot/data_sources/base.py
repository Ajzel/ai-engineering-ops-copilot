
from typing import Any

from ops_copilot.data_sources.synthetic import (
    INCIDENTS,
    LOGS,
    SERVICE_METRICS,
    TRACES,
    DEPLOYMENTS,
)


class SyntheticDataSource:
    """Provide access to synthetic observability datasets."""

    def get_incidents(self) -> dict[str, dict[str, Any]]:
        return INCIDENTS

    def get_logs(self) -> list[dict[str, str]]:
        return LOGS

    def get_service_metrics(self) -> dict[str, dict[str, Any]]:
        return SERVICE_METRICS

    def get_traces(self) -> dict[str, dict[str, Any]]:
        return TRACES

    def get_deployments(self) -> list[dict[str, Any]]:
        return DEPLOYMENTS
