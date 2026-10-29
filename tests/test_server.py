
from ops_copilot.server import (
    list_incidents,
    get_incident_details,
    search_application_logs,
    analyze_incident_tool,
    analyze_error_patterns,
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
