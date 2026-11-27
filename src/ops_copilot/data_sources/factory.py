
from ops_copilot.data_sources.base import SyntheticDataSource
from ops_copilot.data_sources.config import get_data_source_mode


def create_data_source() -> SyntheticDataSource:
    """Create the configured observability data source."""

    mode = get_data_source_mode()

    if mode == "synthetic":
        return SyntheticDataSource()

    raise ValueError(f"Unsupported data source: {mode!r}")
