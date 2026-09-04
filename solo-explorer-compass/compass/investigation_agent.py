"""InvestigationAgent — turns clusters into 'compass headings' with a likely cause.

The similarity agent tells you *what* is happening (a few dominant signatures).
This agent asks *why*, using cheap, explainable evidence gathering:

  - Was there a recent deploy to the failing service, or to something it
    depends on, inside the incident window?  (deploys + dependency graph)
  - Is this cluster actually a downstream/upstream *echo* of a bigger one?
    (dependency graph)  -> if so, don't page a second team for it.
  - Is there a matching runbook and a clear on-call owner?

Confidence is just a function of how much corroborating evidence lines up —
transparent enough to defend in a postmortem. Replace the rules with an LLM
investigation loop if you want (see compass/llm.py); the interface stays the same.
"""
from __future__ import annotations
from datetime import datetime

from .models import Cluster, Finding


def _parse(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


class InvestigationAgent:
    def __init__(self, context: dict):
        self.ctx = context or {}
        self.deploys = self.ctx.get("deploys", [])
        self.edges = self.ctx.get("dependency_graph", [])
        self.runbooks = self.ctx.get("runbooks", {})
        self.oncall = self.ctx.get("oncall", {})
        win = self.ctx.get("incident_window", {})
        self.win_from = _parse(win.get("from", ""))
        self.win_to = _parse(win.get("to", ""))

    # --- public API --------------------------------------------------------
    def investigate(self, clusters: list[Cluster]) -> list[Finding]:
        if not clusters:
            return []
        primary = clusters[0]                      # biggest blast radius
        findings: list[Finding] = []
        for c in clusters:
            findings.append(self._investigate_one(c, primary))
        return findings

    # --- reasoning ---------------------------------------------------------
    def _investigate_one(self, c: Cluster, primary: Cluster) -> Finding:
        evidence: list[str] = []
        service = c.service or self._service_for_api(c.api)

        # 1) is this an echo of the primary cluster? (adjacent in the graph)
        is_echo = c is not primary and self._is_adjacent(service, primary.service)
        if is_echo:
            evidence.append(
                f"{service} is adjacent to {primary.service} in the topology — "
                f"likely a downstream echo, not a separate incident."
            )

        # 2) recent deploy to this service or a dependency, inside the window?
        cause = "unclear from available signals"
        confidence = "low"
        dep = self._recent_deploy_touching(service)
        if dep:
            who, when, change = dep
            if who == service:
                cause = f"recent deploy to {service} ({change})"
            else:
                cause = f"recent deploy to dependency {who} ({change})"
            evidence.append(f"Deploy {who} @ {when} lands inside the incident window.")
            confidence = "high" if c.size >= 5 else "medium"
        elif is_echo:
            cause = f"downstream effect of {primary.errorCode} on {primary.api}"
            confidence = "medium"

        # 3) blast-radius evidence
        if c.size >= 5:
            evidence.append(f"{c.size} correlated alerts across {len(c.hosts)} host(s) — high blast radius.")
        elif c.size == 1:
            evidence.append("Single, isolated alert — watch, don't page.")

        # a lone, non-echo alert shouldn't claim a confident root cause
        if c.size == 1 and not is_echo:
            confidence = "low"

        # 4) runbook + ownership
        rb = self.runbooks.get(c.signature, {})
        runbook = rb.get("url", "")
        if rb:
            evidence.append(f"Matching runbook: {rb.get('name', runbook)}.")
        page = self._page_target(service, dep, is_echo)

        heading = f"errorCode {c.errorCode} + {c.api}"
        return Finding(
            signature=c.signature, heading=heading, size=c.size,
            likely_cause=cause, confidence=confidence, is_echo=is_echo,
            evidence=evidence, page=page, runbook=runbook,
        )

    # --- evidence helpers --------------------------------------------------
    def _service_for_api(self, api: str) -> str:
        return self.ctx.get("api_to_service", {}).get(api, "")

    def _dependencies_of(self, service: str) -> list[str]:
        return [e["to"] for e in self.edges
                if e.get("from") == service and e.get("type") == "depends_on"]

    def _is_adjacent(self, a: str, b: str) -> bool:
        if not a or not b:
            return False
        for e in self.edges:
            f, t = e.get("from"), e.get("to")
            if (f == a and t == b) or (f == b and t == a):
                return True
        return False

    def _recent_deploy_touching(self, service: str):
        """Return (who, when, change) for a deploy to `service` or a dependency
        that falls inside the incident window; else None."""
        candidates = {service, *self._dependencies_of(service)}
        best = None
        for d in self.deploys:
            if d.get("service") not in candidates:
                continue
            when = _parse(d.get("at", ""))
            if when and self.win_from and self.win_to:
                # allow a short lead-in before the window opens
                lead = (self.win_from - when).total_seconds()
                if -1e9 < lead <= 15 * 60 or (self.win_from <= when <= self.win_to):
                    best = (d.get("service"), d.get("at"), d.get("change", "change"))
        return best

    def _page_target(self, service: str, dep, is_echo: bool) -> str:
        if is_echo:
            return "(suppressed — folded into the primary finding)"
        # if a dependency deploy is implicated, page that team primarily
        if dep and dep[0] != service:
            primary_team = self.oncall.get(dep[0], "")
            owner_team = self.oncall.get(service, "")
            teams = [t for t in (primary_team, owner_team) if t]
            return " + ".join(teams) if teams else owner_team
        return self.oncall.get(service, "")
