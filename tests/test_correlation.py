
from ops_copilot.services.correlation import analyze_incident
from ops_copilot.server import INCIDENTS, LOGS


def test_database_incident_analysis():
    result = analyze_incident(INCIDENTS["INC-002"], LOGS)

    assert result["incident_id"] == "INC-002"
    assert result["total_related_logs"] == 2
    assert result["error_log_count"] == 2
    assert result["root_cause"]["status"] == "unconfirmed"


def test_analysis_does_not_mix_incidents():
    result = analyze_incident(INCIDENTS["INC-002"], LOGS)

    assert all(
        log["incident_id"] == "INC-002"
        for finding in result["findings"]
        for log in finding["evidence"]
        if isinstance(log, dict) and "incident_id" in log
    )


def test_analysis_handles_no_logs():
    incident = {
        "id": "INC-TEST",
        "service": "test-service",
        "status": "open",
    }

    result = analyze_incident(incident, [])

    assert result["total_related_logs"] == 0
    assert result["error_log_count"] == 0
    assert result["findings"][0]["severity"] == "info"
