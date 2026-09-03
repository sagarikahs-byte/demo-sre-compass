"""DetectAgent — the Digital Compass's correlation step.

A deliberately *basic* agent: it perceives a flood of alerts, reasons about
which ones are 'the same thing', and acts by collapsing them into a few ranked
clusters. The technique is transparent on purpose — you can read every line and
explain it on stage:

  1. Normalize each alert to a signature (errorCode + API), collapsing volatile
     bits of the path (ids, numbers) so /api/orders/12345 == /api/orders/{id}.
  2. Group by exact signature  -> the bulk of the noise disappears here.
  3. Fuzzy-merge near-duplicate signatures (typos / minor wording) using only
     the standard library's difflib, so no extra installs are needed.
  4. Rank clusters by blast radius (how many alerts, how many hosts).

Swap step 1-3 for an LLM call if you like (see compass/llm.py) — but notice how
far plain, explainable rules already get you. That's the point of the talk.
"""
from __future__ import annotations
import re
from collections import defaultdict
from difflib import SequenceMatcher

from .models import Alert, Cluster

# path segments that look like ids/numbers -> replaced with a placeholder so
# /api/orders/9931 and /api/orders/2210 collapse to the same signature.
_ID_SEG = re.compile(r"/(?:\d+|[0-9a-f]{8,}|[0-9a-f-]{16,})", re.I)


def normalize_api(api: str) -> str:
    return _ID_SEG.sub("/{id}", api or "")


def signature_of(alert: Alert) -> str:
    return f"{alert.errorCode}|{normalize_api(alert.api)}"


class DetectAgent:
    """Correlates raw alerts into a few dominant clusters."""

    def __init__(self, fuzzy_threshold: float = 0.86):
        # how similar two signatures must be to be merged as 'the same'
        self.fuzzy_threshold = fuzzy_threshold

    # --- perceive + reason + act -------------------------------------------
    def correlate(self, alerts: list[Alert]) -> list[Cluster]:
        buckets: dict[str, list[Alert]] = defaultdict(list)
        for a in alerts:
            buckets[signature_of(a)].append(a)

        buckets = self._merge_near_duplicates(buckets)

        clusters: list[Cluster] = []
        for sig, group in buckets.items():
            code, api = sig.split("|", 1)
            # most common service in the group represents the cluster
            service = _mode([a.service for a in group]) or ""
            clusters.append(Cluster(signature=sig, errorCode=code, api=api,
                                    service=service, alerts=group))

        # rank by blast radius: alert count first, then host spread
        clusters.sort(key=lambda c: (c.size, len(c.hosts)), reverse=True)
        return clusters

    # --- helpers -----------------------------------------------------------
    def _merge_near_duplicates(self, buckets: dict[str, list[Alert]]) -> dict[str, list[Alert]]:
        """Fold together signatures that are almost identical (minor wording)."""
        sigs = list(buckets.keys())
        merged: dict[str, list[Alert]] = {}
        used: set[str] = set()
        # process largest first so the dominant signature becomes the canonical name
        sigs.sort(key=lambda s: len(buckets[s]), reverse=True)
        for i, s in enumerate(sigs):
            if s in used:
                continue
            group = list(buckets[s])
            for other in sigs[i + 1:]:
                if other in used:
                    continue
                if SequenceMatcher(None, s, other).ratio() >= self.fuzzy_threshold:
                    group.extend(buckets[other])
                    used.add(other)
            merged[s] = group
            used.add(s)
        return merged


def _mode(values: list[str]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for v in values:
        if v:
            counts[v] += 1
    return max(counts, key=counts.get) if counts else ""
