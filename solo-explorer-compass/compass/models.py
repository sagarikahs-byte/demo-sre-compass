"""Shared data structures for the Solo Explorer's Digital Compass.

Kept intentionally small and dependency-free (standard library only) so the
whole kit runs anywhere with `python run.py` — no installs, no API keys.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Alert:
    """One raw alert as it might arrive from your alerting pipeline."""
    id: str
    ts: str
    errorCode: str
    api: str
    service: str = ""
    host: str = ""
    message: str = ""
    traceId: str = ""
    severity: str = "warning"

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Alert":
        return Alert(
            id=d.get("id", ""), ts=d.get("ts", ""),
            errorCode=str(d.get("errorCode", "")), api=d.get("api", ""),
            service=d.get("service", ""), host=d.get("host", ""),
            message=d.get("message", ""), traceId=d.get("traceId", ""),
            severity=d.get("severity", "warning"),
        )

    @property
    def signature(self) -> str:
        """The compass bearing for an alert: errorCode + API.

        This is the heart of the whole idea — most alert floods are a handful
        of real faults echoing many times. Collapsing to (errorCode + API)
        turns a wall of noise into a few directions to walk in.
        """
        return f"{self.errorCode}|{self.api}"


@dataclass
class Cluster:
    """A group of alerts that share a signature (errorCode + API)."""
    signature: str
    errorCode: str
    api: str
    service: str
    alerts: list[Alert] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.alerts)

    @property
    def hosts(self) -> list[str]:
        return sorted({a.host for a in self.alerts if a.host})


@dataclass
class Finding:
    """The investigation agent's verdict for one cluster — a 'compass heading'."""
    signature: str
    heading: str
    size: int
    likely_cause: str
    confidence: str            # low | medium | high
    is_echo: bool              # True if this is a downstream/upstream echo of another finding
    evidence: list[str] = field(default_factory=list)
    page: str = ""             # who to route to
    runbook: str = ""          # matching runbook, if any
