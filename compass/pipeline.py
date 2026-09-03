"""The Digital Compass pipeline: flood in -> headings out."""
from __future__ import annotations
import json

from .models import Alert
from .detect_agent import DetectAgent
from .investigation_agent import InvestigationAgent


def load_alerts(path: str) -> list[Alert]:
    with open(path, "r", encoding="utf-8") as f:
        return [Alert.from_dict(d) for d in json.load(f)]


def load_context(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_compass(alerts_path: str, context_path: str):
    """Returns (alerts, clusters, findings)."""
    alerts = load_alerts(alerts_path)
    context = load_context(context_path)

    compass = DetectAgent()
    clusters = compass.correlate(alerts)

    investigator = InvestigationAgent(context)
    findings = investigator.investigate(clusters)
    return alerts, clusters, findings
