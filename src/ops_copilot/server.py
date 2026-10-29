
from typing import Any

from mcp.server.fastmcp import FastMCP
from ops_copilot.services.correlation import analyze_incident

mcp = FastMCP("ai-engineering-ops-copilot")

# Synthetic incident data for development and testing.
INCIDENTS: dict[str, dict[str, Any]] = {
    "INC-001": {
        "id": "INC-001",
        "title": "Elevated API response latency",
        "service": "prediction-api",
        "severity": "high",
        "status": "investigating",
        "description": "Prediction requests are slower than usual.",
    },
    "INC-002": {
        "id": "INC-002",
        "title": "Database connection timeout",
        "service": "incident-database",
        "severity": "critical",
        "status": "open",
        "description": "Some requests fail to connect to the database.",
    },
    "INC-003": {
        "id": "INC-003",
        "title": "RAG retrieval slowdown",
        "service": "document-retrieval",
        "severity": "medium",
        "status": "resolved",
        "description": "Document retrieval latency temporarily increased.",
    },
}

LOGS: list[dict[str, str]] = [
    {
        "service": "prediction-api",
        "level": "WARNING",
        "message": "Prediction latency exceeded 2000 ms",
        "incident_id": "INC-001",
    },
    {
        "service": "prediction-api",
        "level": "ERROR",
        "message": "Prediction request timed out after 5000 ms",
        "incident_id": "INC-001",
    },
    {
        "service": "incident-database",
        "level": "ERROR",
        "message": "Database connection pool exhausted",
        "incident_id": "INC-002",
    },
    {
        "service": "incident-database",
        "level": "ERROR",
        "message": "Database connection attempt timed out",
        "incident_id": "INC-002",
    },
    {
        "service": "document-retrieval",
        "level": "WARNING",
        "message": "Vector search latency exceeded threshold",
        "incident_id": "INC-003",
    },
]


@mcp.tool()
def list_incidents(
    severity: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """List incidents with optional severity and status filters."""

    # Normalize optional filters to handle None and whitespace.
    severity = (severity or "").strip().lower()
    status = (status or "").strip().lower()

    # Validate the result limit.
    if not 1 <= limit <= 100:
        return {"error": "limit must be between 1 and 100"}

    # Validate severity filter.
    if severity and severity not in {
        "critical", "high", "medium", "low"
    }:
        return {"error": "Invalid severity filter"}

    # Validate status filter.
    if status and status not in {
        "open", "investigating", "resolved"
    }:
        return {"error": "Invalid status filter"}

    # Apply filters.
    results = [
        item
        for item in INCIDENTS.values()
        if (not severity or item["severity"] == severity)
        and (not status or item["status"] == status)
    ]

    # Apply limit and return results.
    limited_results = results[:limit]

    return {
        "count": len(limited_results),
        "incidents": limited_results,
    }


@mcp.tool()
def get_incident_details(incident_id: str) -> dict[str, Any]:
    """Return an incident and its associated application logs."""
    incident_id = incident_id.strip().upper()
    incident = INCIDENTS.get(incident_id)

    if incident is None:
        return {"error": f"Incident not found: {incident_id}"}

    related_logs = [
        log for log in LOGS if log["incident_id"] == incident_id
    ]

    return {"incident": incident, "related_logs": related_logs}


@mcp.tool()
def search_application_logs(
    query: str = "",
    service: str = "",
    level: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    """Search application logs by message, service name, or log level."""
    if not 1 <= limit <= 100:
        return {"error": "limit must be between 1 and 100"}

    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level and level.upper() not in allowed_levels:
        return {"error": "Invalid log level"}

    query = query.strip().lower()
    service = service.strip().lower()
    level = level.strip().upper()

    results = [
        log
        for log in LOGS
        if query in log["message"].lower()
        and (not service or service in log["service"].lower())
        and (not level or log["level"] == level)
    ]

    return {"count": len(results[:limit]), "logs": results[:limit]}


@mcp.tool()
def analyze_error_patterns(
    service: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Group application errors by message and report their frequency."""

    if not 1 <= limit <= 100:
        return {"error": "limit must be between 1 and 100"}

    service = (service or "").strip().lower()

    # Use the existing application log dataset.
    matching_logs = [
        log
        for log in LOGS
        if str(log.get("level", "")).upper() in {"ERROR", "CRITICAL"}
        and (
            not service
            or str(log.get("service", "")).lower() == service
        )
    ]

    # Group errors using their exact message text.
    patterns: dict[str, dict[str, Any]] = {}

    for log in matching_logs:
        message = str(log.get("message", "Unknown error")).strip()
        log_service = log.get("service", "unknown")

        if message not in patterns:
            patterns[message] = {
                "message": message,
                "count": 0,
                "services": [],
                "levels": [],
            }

        pattern = patterns[message]
        pattern["count"] += 1

        if log_service not in pattern["services"]:
            pattern["services"].append(log_service)

        level = str(log.get("level", "UNKNOWN")).upper()
        if level not in pattern["levels"]:
            pattern["levels"].append(level)

    ranked_patterns = sorted(
        patterns.values(),
        key=lambda item: (-item["count"], item["message"]),
    )

    results = ranked_patterns[:limit]

    return {
        "service_filter": service or None,
        "total_matching_logs": len(matching_logs),
        "unique_error_patterns": len(patterns),
        "returned_patterns": len(results),
        "patterns": results,
        "data_source": "synthetic application logs",
    }

@mcp.tool()
def analyze_incident_tool(incident_id: str) -> dict[str, Any]:
    """Analyze an incident and its associated logs.

    Returns evidence-based findings. Root cause is not confirmed
    automatically; findings summarize observed log activity.
    """
    normalized_id = incident_id.strip().upper()
    incident = INCIDENTS.get(normalized_id)

    if incident is None:
        return {"error": f"Incident not found: {normalized_id}"}

    return analyze_incident(incident, LOGS)



if __name__ == "__main__":
    mcp.run(transport="stdio")
