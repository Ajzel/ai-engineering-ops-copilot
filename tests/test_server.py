
from ops_copilot.server import (
    list_incidents,
    get_incident_details,
    search_application_logs,
    analyze_incident_tool,
    analyze_error_patterns,
    get_service_metrics,
    get_trace_details,
    get_deployment_history,
    correlate_incident_changes,
)


def test_list_incidents():
    result = list_incidents()
    assert result["count"] == 3

def test_list_incidents_accepts_none_filters():
    result = list_incidents(severity=None, status=None)

    assert result["count"] == 3
    assert len(result["incidents"]) == 3

def test_filter_incidents_by_severity():
    result = list_incidents(severity="high")
    assert result["count"] == 1
    assert result["incidents"][0]["id"] == "INC-001"


def test_get_incident_details():
    result = get_incident_details("INC-002")
    assert result["incident"]["severity"] == "critical"
    assert len(result["related_logs"]) == 2


def test_unknown_incident():
    result = get_incident_details("INC-999")
    assert "error" in result


def test_search_error_logs():
    result = search_application_logs(
        query="timed out",
        level="ERROR",
    )
    assert result["count"] == 2


def test_invalid_limit():
    result = list_incidents(limit=0)
    assert "error" in result


def test_analyze_incident_tool():
    result = analyze_incident_tool("INC-002")

    assert result["incident_id"] == "INC-002"
    assert result["service"] == "incident-database"
    assert result["error_log_count"] == 2
    assert result["root_cause"]["status"] == "unconfirmed"


def test_analyze_incident_tool_case_insensitive():
    result = analyze_incident_tool("inc-002")

    assert result["incident_id"] == "INC-002"


def test_analyze_incident_tool_unknown_incident():
    result = analyze_incident_tool("INC-999")

    assert result == {"error": "Incident not found: INC-999"}


def test_analyze_error_patterns_returns_summary():
    result = analyze_error_patterns()

    assert "error" not in result
    assert result["data_source"] == "synthetic application logs"
    assert result["total_matching_logs"] >= 0
    assert result["unique_error_patterns"] >= 0
    assert result["returned_patterns"] == len(result["patterns"])

    for pattern in result["patterns"]:
        assert pattern["count"] > 0
        assert pattern["message"]
        assert pattern["services"]
        assert pattern["levels"]


def test_analyze_error_patterns_filters_by_service():
    result = analyze_error_patterns(service="incident-database")

    assert "error" not in result
    assert result["service_filter"] == "incident-database"

    for pattern in result["patterns"]:
        assert all(
            service.lower() == "incident-database"
            for service in pattern["services"]
        )


def test_analyze_error_patterns_rejects_invalid_limit():
    result = analyze_error_patterns(limit=0)

    assert result == {
        "error": "limit must be between 1 and 100"
    }


def test_get_service_metrics_returns_known_service():
    result = get_service_metrics(service="incident-database")

    assert result["service"] == "incident-database"
    assert result["is_simulated"] is True
    assert result["metrics"]["response_latency_ms"] > 0


def test_get_service_metrics_is_case_insensitive():
    result = get_service_metrics(service="INCIDENT-DATABASE")

    assert result["service"] == "incident-database"


def test_get_service_metrics_rejects_unknown_service():
    result = get_service_metrics(service="unknown-service")

    assert result["error"] == "Unknown service: unknown-service"
    assert "incident-database" in result["available_services"]


def test_get_service_metrics_returns_all_services():
    result = get_service_metrics()

    assert result["count"] == 3
    assert result["is_simulated"] is True
    assert "prediction-api" in result["services"]
    assert "incident-database" in result["services"]
    assert "document-retrieval" in result["services"]


def test_get_trace_details_returns_known_trace():
    result = get_trace_details("trace-002")

    assert "error" not in result
    assert result["trace"]["trace_id"] == "trace-002"
    assert result["trace"]["incident_id"] == "INC-002"
    assert len(result["trace"]["spans"]) == 2
    assert result["is_simulated"] is True
    assert result["data_source"] == "synthetic development data"


def test_get_trace_details_returns_span_information():
    result = get_trace_details("trace-001")

    span = result["trace"]["spans"][0]

    assert span["service"] == "prediction-api"
    assert span["operation"] == "predict"
    assert span["duration_ms"] > 0
    assert span["status"] == "error"


def test_get_trace_details_handles_unknown_trace():
    result = get_trace_details("trace-999")

    assert result["error"] == "Trace not found: trace-999"
    assert "trace-001" in result["available_trace_ids"]


def test_get_trace_details_rejects_empty_trace_id():
    result = get_trace_details("   ")

    assert result == {"error": "trace_id must not be empty"}

def test_get_all_deployments():
    result = get_deployment_history()

    assert result["total_deployments"] == 4
    assert result["returned_deployments"] == 4
    assert result["is_simulated"] is True
    assert len(result["deployments"]) == 4


def test_filter_deployments_by_service():
    result = get_deployment_history(service="incident-database")

    assert result["total_deployments"] == 2

    for deployment in result["deployments"]:
        assert deployment["service"] == "incident-database"


def test_filter_deployments_by_environment():
    result = get_deployment_history(environment="production")

    assert result["total_deployments"] == 3

    for deployment in result["deployments"]:
        assert deployment["environment"] == "production"


def test_filter_deployments_by_service_and_environment():
    result = get_deployment_history(
        service="incident-database",
        environment="production",
    )

    assert result["total_deployments"] == 2

    for deployment in result["deployments"]:
        assert deployment["service"] == "incident-database"
        assert deployment["environment"] == "production"


def test_deployment_limit_validation():
    result = get_deployment_history(limit=0)

    assert "error" in result
    assert "between 1 and 100" in result["error"]


def test_unknown_service_returns_empty_results():
    result = get_deployment_history(service="unknown-service")

    assert result["total_deployments"] == 0
    assert result["returned_deployments"] == 0
    assert result["deployments"] == []


def test_deployment_data_is_simulated():
    result = get_deployment_history()

    assert result["data_source"] == "synthetic development data"
    assert result["is_simulated"] is True


def test_deployment_filters_are_case_insensitive():
    result = get_deployment_history(
        service="INCIDENT-DATABASE",
        environment="PRODUCTION",
    )

    assert result["total_deployments"] == 2
    
def test_correlate_incident_changes_returns_incident():
    result = correlate_incident_changes("INC-002")

    assert result["incident_id"] == "INC-002"
    assert result["incident_title"] == "Database connection timeout"
    assert result["service"] == "incident-database"


def test_correlate_incident_changes_finds_deployments():
    result = correlate_incident_changes("INC-002")

    candidates = result["deployment_analysis"]["candidates"]

    assert len(candidates) == 2

    deployment_ids = [
        deployment["deployment_id"]
        for deployment in candidates
    ]

    assert "DEP-002" in deployment_ids
    assert "DEP-003" in deployment_ids


def test_correlate_incident_changes_identifies_matching_terms():
    result = correlate_incident_changes("INC-002")

    candidates = result["deployment_analysis"]["candidates"]

    dep003 = next(
        deployment
        for deployment in candidates
        if deployment["deployment_id"] == "DEP-003"
    )

    assert "connection" in dep003["matched_terms"]
    assert "pool" in dep003["matched_terms"]
    assert dep003["relevance"] == "potentially_relevant"


def test_correlate_incident_changes_returns_related_logs():
    result = correlate_incident_changes("INC-002")

    logs = result["incident_evidence"]["related_logs"]

    assert len(logs) == 2

    messages = [
        log["message"]
        for log in logs
    ]

    assert any("pool exhausted" in message for message in messages)
    assert any("timed out" in message for message in messages)


def test_correlate_incident_changes_does_not_establish_causation():
    result = correlate_incident_changes("INC-002")

    assessment = result["correlation_assessment"]

    assert assessment["causation_established"] is False
    assert "does not establish" in assessment["conclusion"]


def test_correlate_incident_changes_identifies_simulated_data():
    result = correlate_incident_changes("INC-002")

    assert result["is_simulated"] is True
    assert result["data_source"] == "synthetic development data"


def test_correlate_incident_changes_handles_unknown_incident():
    result = correlate_incident_changes("INC-999")

    assert "error" in result
    assert result["incident_id"] == "INC-999"


def test_correlate_incident_changes_rejects_empty_id():
    result = correlate_incident_changes("")

    assert "error" in result
    assert result["error"] == "Incident ID cannot be empty."