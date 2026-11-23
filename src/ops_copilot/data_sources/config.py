
import os

SUPPORTED_DATA_SOURCES = {"synthetic"}


def get_data_source_mode() -> str:
    """Return the configured observability data-source mode."""

    mode = os.getenv(
        "OPS_COPILOT_DATA_SOURCE", "synthetic"
    ).strip().lower()

    if mode not in SUPPORTED_DATA_SOURCES:
        raise ValueError(
            f"Unsupported data source: {mode!r}. "
            "Currently supported: synthetic."
        )

    return mode
