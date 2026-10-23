"""Cost estimates shown before `cheat-index run` starts: measured cost per run where we have it, otherwise a
token assumption per harness times the model's current OpenRouter price."""

from __future__ import annotations

import json
from typing import Any

from cheat_index.paths import package_data


def cost_model() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(package_data("cost_model.json").read_text(encoding="utf-8"))
    return data


def _model_price(model: str) -> tuple[float, float] | None:
    import httpx

    try:
        resp = httpx.get("https://openrouter.ai/api/v1/models", timeout=20)
        for m in resp.json().get("data", []):
            if m.get("id") == model:
                p = m.get("pricing") or {}
                return float(p.get("prompt", 0)), float(p.get("completion", 0))
    except (httpx.HTTPError, ValueError, TypeError):
        return None
    return None


def estimate_per_run(agent: str, model: str) -> tuple[float | None, str]:
    cm = cost_model()
    measured = cm.get("measured", {}).get(f"{agent}|{model}")
    if measured:
        return float(measured["usd_per_run"]), f"measured over {measured['runs']} runs on {measured['date']}"
    tokens = cm.get("tokens_per_run", {}).get(agent)
    price = _model_price(model)
    if not tokens or price is None:
        return None, "no measurement for this agent and model, and no price found"
    usd = tokens["prompt"] * price[0] * tokens.get("uncached_share", 1.0) + tokens["completion"] * price[1]
    return (
        usd,
        f"assumed {tokens['prompt'] // 1000}k prompt / {tokens['completion'] // 1000}k completion tokens per run",
    )
