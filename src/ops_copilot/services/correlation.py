
from collections import Counter
from typing import Any


def analyze_incident(
    incident: dict[str, Any],
    logs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze incident logs and return evidence-backed findings."""

    incident_id = incident.get("id", "unknown")
    service = incident.get("service", "unknown")

    related_logs = [
        log
        for log in logs
        if log.get("incident_id") == incident_id
    ]

    error_logs = [
        log
        for log in related_logs
        if log.get("level", "").upper() in {"ERROR", "CRITICAL"}
    ]

    message_counts = Counter(
        log.get("message", "Unknown message")
        for log in error_logs
    )

    findings = []

    if error_logs:
        findings.append({
            "category": "error_activity",
            "severity": "high" if len(error_logs) >= 2 else "medium",
            "observation": (
                f"Found {len(error_logs)} error-level log entries "
                f"associated with {incident_id}."
            ),
            "evidence": error_logs,
            "confidence": "high",
        })
    else:
        findings.append({
            "category": "error_activity",
            "severity": "info",
            "observation": "No error-level logs were found for this incident.",
            "evidence": [],
            "confidence": "high",
        })

    if message_counts:
        repeated_messages = [
            {"message": message, "count": count}
            for message, count in message_counts.items()
            if count > 1
        ]

        if repeated_messages:
            findings.append({
                "category": "repeated_errors",
                "severity": "medium",
                "observation": "Repeated error messages were detected.",
                "evidence": repeated_messages,
                "confidence": "high",
            })

    return {
        "incident_id": incident_id,
        "service": service,
        "incident_status": incident.get("status", "unknown"),
        "total_related_logs": len(related_logs),
        "error_log_count": len(error_logs),
        "findings": findings,
        "root_cause": {
            "status": "unconfirmed",
            "statement": (
                "Insufficient evidence to confirm a root cause. "
                "The findings describe observed log activity only."
            ),
        },
    }
