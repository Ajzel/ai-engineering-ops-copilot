from typing import Any

# Synthetic observability data for development and testing.

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
