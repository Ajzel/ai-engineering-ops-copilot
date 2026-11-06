import re
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


# Synthetic service metrics for local development and testing.
# These values are simulated, not live production measurements.
SERVICE_METRICS: dict[str, dict[str, Any]] = {
    "prediction-api": {
        "response_latency_ms": 240.0,
        "error_rate_percent": 2.5,
        "requests_per_minute": 1200,
        "cpu_usage_percent": 65.0,
        "memory_usage_percent": 72.0,
    },
    "incident-database": {
        "response_latency_ms": 850.0,
        "error_rate_percent": 8.0,
        "requests_per_minute": 900,
        "cpu_usage_percent": 78.0,
        "memory_usage_percent": 84.0,
    },
    "document-retrieval": {
        "response_latency_ms": 310.0,
        "error_rate_percent": 1.2,
        "requests_per_minute": 450,
        "cpu_usage_percent": 48.0,
        "memory_usage_percent": 60.0,
    },
}


# Synthetic distributed traces for local development and testing.
# These traces are simulated, not collected from a production tracing system.
TRACES: dict[str, dict[str, Any]] = {
    "trace-001": {
        "trace_id": "trace-001",
        "incident_id": "INC-001",
        "status": "error",
        "total_duration_ms": 5230.0,
        "spans": [
            {
                "span_id": "span-001",
                "service": "prediction-api",
                "operation": "predict",
                "duration_ms": 5230.0,
                "status": "error",
                "error": "Prediction request timed out after 5000 ms",
            },
        ],
    },
    "trace-002": {
        "trace_id": "trace-002",
        "incident_id": "INC-002",
        "status": "error",
        "total_duration_ms": 1850.0,
        "spans": [
            {
                "span_id": "span-002",
                "service": "incident-database",
                "operation": "acquire_connection",
                "duration_ms": 1000.0,
                "status": "error",
                "error": "Database connection pool exhausted",
            },
            {
                "span_id": "span-003",
                "service": "incident-database",
                "operation": "connect",
                "duration_ms": 850.0,
                "status": "error",
                "error": "Database connection attempt timed out",
            },
        ],
    },
    "trace-003": {
        "trace_id": "trace-003",
        "incident_id": "INC-003",
        "status": "ok",
        "total_duration_ms": 310.0,
        "spans": [
            {
                "span_id": "span-004",
                "service": "document-retrieval",
                "operation": "vector_search",
                "duration_ms": 310.0,
                "status": "ok",
                "error": None,
            },
        ],
    },
}

DEPLOYMENTS: list[dict[str, Any]] = [
    {
        "deployment_id": "DEP-001",
        "service": "prediction-api",
        "version": "v1.2.0",
        "environment": "production",
        "deployed_at": "2026-10-28T10:30:00Z",
        "status": "successful",
        "changes": "Updated prediction API response handling.",
    },
    {
        "deployment_id": "DEP-002",
        "service": "incident-database",
        "version": "v2.1.0",
        "environment": "production",
        "deployed_at": "2026-10-29T14:00:00Z",
        "status": "successful",
        "changes": "Updated database connection configuration.",
    },
    {
        "deployment_id": "DEP-003",
        "service": "incident-database",
        "version": "v2.1.1",
        "environment": "production",
        "deployed_at": "2026-10-30T09:15:00Z",
        "status": "failed",
        "changes": "Attempted database connection pool adjustment.",
    },
    {
        "deployment_id": "DEP-004",
        "service": "document-retrieval",
        "version": "v1.4.0",
        "environment": "staging",
        "deployed_at": "2026-10-31T11:45:00Z",
        "status": "successful",
        "changes": "Optimized vector search processing.",
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
def get_service_metrics(
    service: str | None = None,
) -> dict[str, Any]:
    """Retrieve simulated health metrics for known services."""

    service = (service or "").strip().lower()

    if service:
        metrics = SERVICE_METRICS.get(service)

        if metrics is None:
            return {
                "error": f"Unknown service: {service}",
                "available_services": sorted(SERVICE_METRICS),
            }

        return {
            "service": service,
            "metrics": metrics.copy(),
            "data_source": "synthetic development data",
            "is_simulated": True,
        }

    return {
        "services": {
            name: metrics.copy()
            for name, metrics in sorted(SERVICE_METRICS.items())
        },
        "count": len(SERVICE_METRICS),
        "data_source": "synthetic development data",
        "is_simulated": True,
    }



@mcp.tool()
def get_trace_details(trace_id: str) -> dict[str, Any]:
    """Retrieve a synthetic distributed trace by its trace ID."""

    trace_id = (trace_id or "").strip()

    if not trace_id:
        return {"error": "trace_id must not be empty"}

    trace = TRACES.get(trace_id)

    if trace is None:
        return {
            "error": f"Trace not found: {trace_id}",
            "available_trace_ids": sorted(TRACES.keys()),
        }

    # Return a copy so callers cannot mutate the stored trace data.
    return {
        "trace": {
            **trace,
            "spans": [span.copy() for span in trace["spans"]],
        },
        "data_source": "synthetic development data",
        "is_simulated": True,
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

@mcp.tool()
def get_deployment_history(
    service: str | None = None,
    environment: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Retrieve deployment history with optional service
    and environment filters.
    """

    service = (service or "").strip().lower()
    environment = (environment or "").strip().lower()

    if not 1 <= limit <= 100:
        return {
            "error": "Limit must be between 1 and 100."
        }

    deployments = DEPLOYMENTS.copy()

    if service:
        deployments = [
            deployment
            for deployment in deployments
            if deployment["service"].lower() == service
        ]

    if environment:
        deployments = [
            deployment
            for deployment in deployments
            if deployment["environment"].lower() == environment
        ]

    deployments.sort(
        key=lambda deployment: deployment["deployed_at"],
        reverse=True,
    )

    return {
        "data_source": "synthetic development data",
        "is_simulated": True,
        "filters": {
            "service": service or None,
            "environment": environment or None,
        },
        "total_deployments": len(deployments),
        "returned_deployments": len(deployments[:limit]),
        "deployments": deployments[:limit],
    }

@mcp.tool()
def correlate_incident_changes(
    incident_id: str,
) -> dict[str, Any]:
    """
    Correlate an incident with deployment changes associated
    with the same service.

    Identifies potential relationships using shared service
    names and matching terms in incident evidence and
    deployment descriptions.

    Correlation does not establish causation.
    """

    incident_id = (incident_id or "").strip().upper()

    if not incident_id:
        return {
            "error": "Incident ID cannot be empty."
        }

    # 1. Retrieve the incident
    incident = INCIDENTS.get(incident_id)

    if not incident:
        return {
            "error": f"Incident {incident_id} was not found.",
            "incident_id": incident_id,
        }

    service = incident.get("service", "")

    # 2. Retrieve logs associated with the incident
    incident_logs = [
        log
        for log in LOGS
        if log.get("incident_id", "").upper() == incident_id
    ]

    # 3. Build searchable incident evidence
    incident_text = " ".join([
        str(incident.get("title", "")),
        str(incident.get("description", "")),
        *[
            str(log.get("message", ""))
            for log in incident_logs
        ],
    ]).lower()

    stopwords = {
        "the", "and", "for", "with", "from", "that",
        "this", "was", "were", "has", "have", "had",
        "some", "requests", "request", "service",
        "updated", "update", "attempted", "attempt",
    }

    incident_terms = {
        term
        for term in re.findall(r"[a-z0-9]+", incident_text)
        if len(term) > 2 and term not in stopwords
    }

    # 4. Retrieve deployments belonging to the same service
    service_deployments = [
        deployment
        for deployment in DEPLOYMENTS
        if deployment.get("service", "").lower() == service.lower()
    ]

    # 5. Compare deployment descriptions with incident evidence
    candidates = []

    for deployment in service_deployments:
        change_description = str(
            deployment.get("changes", "")
        )

        deployment_terms = {
            term
            for term in re.findall(
                r"[a-z0-9]+",
                change_description.lower(),
            )
            if len(term) > 2 and term not in stopwords
        }

        matched_terms = sorted(
            incident_terms.intersection(deployment_terms)
        )

        if matched_terms:
            relevance = "potentially_relevant"
        else:
            relevance = "same_service_only"

        candidates.append({
            "deployment_id": deployment.get("deployment_id"),
            "service": deployment.get("service"),
            "version": deployment.get("version"),
            "environment": deployment.get("environment"),
            "deployed_at": deployment.get("deployed_at"),
            "status": deployment.get("status"),
            "changes": change_description,
            "matched_terms": matched_terms,
            "relevance": relevance,
        })

    # 6. Return evidence and limitations
    return {
        "incident_id": incident_id,
        "incident_title": incident.get("title"),
        "service": service,

        "data_source": "synthetic development data",
        "is_simulated": True,

        "incident_evidence": {
            "description": incident.get("description"),
            "related_logs": [
                {
                    "level": log.get("level"),
                    "service": log.get("service"),
                    "message": log.get("message"),
                }
                for log in incident_logs
            ],
        },

        "deployment_analysis": {
            "total_service_deployments": len(service_deployments),
            "candidates": candidates,
        },

        "correlation_assessment": {
            "status": "potential_relationships_identified"
            if candidates else "no_matching_deployments",
            "matching_basis": [
                "Same service",
                "Shared terms between incident evidence and deployment descriptions",
            ],
            "causation_established": False,
            "conclusion": (
                "Deployment records contain potential investigation "
                "candidates. The available evidence does not establish "
                "that any deployment caused the incident."
            ),
        },

        "evidence_gaps": [
            "Incident logs do not contain timestamps.",
            "Historical time-series metrics are not available.",
            "Deployment configuration diffs are not available.",
            "Post-deployment health checks are not available.",
        ],
    }




if __name__ == "__main__":
    mcp.run(transport="stdio")

