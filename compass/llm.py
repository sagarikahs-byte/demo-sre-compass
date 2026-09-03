"""Optional, vendor-neutral LLM hook.

The kit runs fully offline with the rule-based agents. If you want to see how an
LLM would slot in — for messier, free-text alerts where exact signatures aren't
obvious — implement `call_llm` for whatever provider you use and flip
`USE_LLM = True`. Nothing else in the kit needs to change.

Deliberately provider-agnostic: no SDK, no product name, no key handling here.
"The pattern matters, not the product."
"""
from __future__ import annotations

USE_LLM = False


def call_llm(system: str, user: str) -> str:
    """Return the model's text response. Left unimplemented on purpose.

    Example shape (pseudocode) — wire to any chat/completions endpoint:

        client = your_provider.Client(api_key=os.environ["YOUR_KEY"])
        resp = client.messages.create(
            model="<your-model>",
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.text

    In an MCP setup, the same model would also be given *tools* (query logs,
    fetch a runbook, look up recent deploys) instead of being handed context
    inline — but the correlation/investigation idea is identical.
    """
    raise NotImplementedError(
        "LLM mode is off. Set USE_LLM = True and implement call_llm() to enable it."
    )


def suggest_signature_llm(message: str) -> str:
    """Illustrative helper: ask an LLM to extract an (errorCode + API) signature
    from a free-text alert. Only used when USE_LLM is True."""
    system = ("You are an SRE triage assistant. Given one alert line, reply with "
              "just 'errorCode|api' — no prose.")
    return call_llm(system, message).strip()
