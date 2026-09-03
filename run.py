#!/usr/bin/env python3
"""Run the Digital Compass on a set of alerts.

    python run.py                          # noisy sample + sample context
    python run.py --alerts data/alerts_clean.json
    python run.py --no-color               # plain output for slides/screenshots

No dependencies beyond the Python standard library. Nothing leaves your machine.
"""
from __future__ import annotations
import argparse
import os
import sys

from compass.pipeline import run_compass

HERE = os.path.dirname(os.path.abspath(__file__))


# --- tiny ANSI helper (auto-disables when not a TTY) -----------------------
class C:
    enabled = sys.stdout.isatty()

    @classmethod
    def _w(cls, code, s):
        return f"\033[{code}m{s}\033[0m" if cls.enabled else s

    @classmethod
    def bold(cls, s): return cls._w("1", s)
    @classmethod
    def dim(cls, s): return cls._w("2", s)
    @classmethod
    def magenta(cls, s): return cls._w("38;5;169", s)
    @classmethod
    def cyan(cls, s): return cls._w("38;5;38", s)
    @classmethod
    def green(cls, s): return cls._w("38;5;42", s)
    @classmethod
    def grey(cls, s): return cls._w("38;5;103", s)


def rule(char="─", n=64):
    print(C.grey(char * n))


def main() -> int:
    ap = argparse.ArgumentParser(description="The Solo Explorer's Digital Compass")
    ap.add_argument("--alerts", default=os.path.join(HERE, "data", "alerts_noisy.json"))
    ap.add_argument("--context", default=os.path.join(HERE, "data", "context.json"))
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    if args.no_color:
        C.enabled = False

    alerts, clusters, findings = run_compass(args.alerts, args.context)

    # ---- BEFORE: the flood ------------------------------------------------
    print()
    print(C.bold("  🧭  THE DIGITAL COMPASS"))
    print(C.dim("      from a wall of alerts to a few clear headings"))
    print()
    rule()
    print(C.bold(f"  SURVIVAL MODE — {len(alerts)} raw alerts firing"))
    rule()
    preview = alerts[:8]
    for a in preview:
        print("   " + C.magenta(f"{a.errorCode:<8}") + C.grey(f"{a.api:<16}") +
              C.dim(f"{a.host:<16} {a.message[:34]}"))
    if len(alerts) > len(preview):
        print(C.dim(f"   … and {len(alerts) - len(preview)} more"))
    print()

    # ---- AFTER: the headings ---------------------------------------------
    rule("═")
    signals = [f for f in findings if not f.is_echo]
    echoes = sum(1 for f in findings if f.is_echo)
    dups_collapsed = (findings[0].size - 1) if findings else 0
    print(C.bold(f"  WELLNESS MODE — {len(signals)} signals to act on "
                 f"({len(alerts)} alerts in, noise filtered)"))
    rule("═")
    print()

    for i, f in enumerate(findings):
        is_primary = (i == 0)
        tag = (C.magenta(C.bold("PRIMARY")) if is_primary
               else (C.dim("echo   ") if f.is_echo else C.cyan("minor  ")))
        print(f"  {tag}  " + C.bold(f.heading) +
              C.dim(f"   ×{f.size}  ({_pct(f.size, len(alerts))} of flood)"))
        print("          " + C.grey("likely cause: ") + f.likely_cause +
              C.dim(f"   [confidence: {f.confidence}]"))
        for e in f.evidence:
            print("            " + C.grey("• ") + C.dim(e))
        if f.page:
            print("          " + C.grey("page: ") + C.green(f.page))
        if f.runbook:
            print("          " + C.grey("runbook: ") + f.runbook)
        print()

    # ---- one-line takeaway ------------------------------------------------
    rule()
    top = findings[0] if findings else None
    if top:
        print("  " + C.bold("Heading: ") + C.magenta(top.heading) +
              C.dim(f"  —  {dups_collapsed} duplicates collapsed, {echoes} echo suppressed."))
    print("  " + C.dim(f"{len(alerts)} raw alerts  →  {len(signals)} signals to act on."))
    print(C.dim("  Noise became a heading. That's the bridge from survival to wellness."))
    print()
    return 0


def _pct(n, total):
    return f"{(100.0 * n / total):.0f}%" if total else "0%"


if __name__ == "__main__":
    raise SystemExit(main())
