# 🧭 The Solo Explorer's Digital Compass

*A tiny, runnable companion to the GHC 2026 session "The Solo Explorer's Guide to SRE: Navigating the Unknown with AI."*

An outage is a journey into the unknown: a flood of alerts, no map, and often just you. This kit is the **Digital Compass** from the talk — a pair of small, transparent agents that turn a wall of noisy alerts into a few clear headings, so you spend your energy on signal instead of noise.

It runs **offline, on the Python standard library alone** — no installs, no API keys, nothing leaves your machine. Fork it, read it, break it, make it yours.

---

## Quickstart

```bash
git clone <your-fork-url>
cd solo-explorer-compass
python run.py
```

You'll see a **before** (40 raw alerts, "survival mode") collapse into an **after** (a few ranked headings, "wellness mode"), with a likely root cause for each.

```
python run.py                                   # noisy sample flood
python run.py --alerts data/alerts_clean.json   # smaller example set
python run.py --no-color                        # plain text (good for screenshots)
```

---

## What's inside

```
solo-explorer-compass/
├── run.py                     # CLI: flood in → headings out
├── data/
│   ├── alerts_clean.json      # small, representative example alerts
│   ├── alerts_noisy.json      # the flood: 40 alerts, mostly echoes of a few faults
│   └── context.json           # deploys, service topology, on-call owners
└── compass/
    ├── models.py              # Alert, Cluster, Finding
    ├── detect_agent.py        # ① correlate the flood  (the "compass bearing")
    ├── investigation_agent.py # ② find the likely root cause  (the "why")
    ├── llm.py                 # optional, vendor-neutral LLM hook (off by default)
    └── pipeline.py            # ties the two agents together
```

## The two agents

**① DetectAgent — the correlation step.** Perceives the flood, reasons about which alerts are "the same thing," and collapses them into a few ranked clusters. It's deliberately basic and explainable:

1. Normalize each alert to a **signature = `errorCode + API`** (collapsing volatile path ids so `/api/orders/9931` and `/api/orders/2210` match).
2. Group by exact signature — most of the noise disappears here.
3. Fuzzy-merge near-duplicate signatures with the standard library's `difflib` (no installs).
4. Rank clusters by **blast radius** (alert count, host spread).

**② InvestigationAgent — the "why."** Takes the clusters and gathers cheap, defensible evidence from `context.json`:

- Was there a **recent deploy** to the failing service *or to something it depends on*, inside the incident window?  (deploys + dependency graph)
- Is this cluster actually a **downstream echo** of a bigger one (adjacent in the dependency graph)? If so, don't page a second team for it.
- Who's the **on-call owner** to route the one clear page to?

Confidence is just a function of how much evidence lines up — transparent enough to defend in a postmortem.

On the sample data, 40 alerts become **one primary heading** — `errorCode 503 + /api/checkout`, likely caused by a recent `auth-service` deploy (an `infra-service` dependency) — with the gateway 5xx flagged as an echo and the rest as low-signal.

## Want to add an LLM?

The kit works fully without one. When alerts are messier free text and exact signatures aren't obvious, an LLM helps. `compass/llm.py` is a **vendor-neutral stub** — implement `call_llm()` for whatever provider you use and set `USE_LLM = True`. In an MCP setup the same model would be given *tools* (query logs, fetch a runbook, look up deploys) rather than inline context, but the correlation/investigation idea is identical. *The pattern matters, not the product.*

## Make it yours (the self-guided workshop)

See [`WORKSHOP.md`](WORKSHOP.md) for three short exercises: run a **noise audit** on your own alerts, extend the **compass** with a new signal, and use the **mindset checklist** on your next solo incident.

---

*Shared as a takeaway from GHC 2026. MIT licensed — use it, teach with it, build on it.*
