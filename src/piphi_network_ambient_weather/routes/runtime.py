from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ..contract import ENDPOINTS, REQUIRED_ENDPOINTS
from ..settings import (
    INTEGRATION_ID,
    INTEGRATION_NAME,
    INTEGRATION_VERSION,
    PROJECT_DOMAIN,
    PROJECT_KIND,
    PROJECT_PRESET,
)
from ..state import registry

router = APIRouter(tags=["runtime"])


def _public_entries() -> dict[str, Any]:
    secret_fields = {"api_key", "application_key"}
    result: dict[str, Any] = {}
    for key, entry in registry.entries.items():
        public = {name: value for name, value in entry.items() if name != "config"}
        config = entry.get("config", {})
        public["config"] = {name: ("***" if name in secret_fields and value is not None else value) for name, value in config.items()}
        result[key] = public
    return result


@router.get("/state")
async def state() -> dict[str, Any]:
    return {
        "summary": {
            "active_config_count": len(registry.ids()),
            "recent_event_count": len(registry.recent_events),
        },
        "entries": _public_entries(),
        "state_snapshots": registry.state_snapshots,
    }


@router.get("/contract")
async def contract() -> dict[str, Any]:
    return {
        "integration_id": INTEGRATION_ID,
        "name": INTEGRATION_NAME,
        "version": INTEGRATION_VERSION,
        "kind": PROJECT_KIND,
        "preset": PROJECT_PRESET,
        "domain": PROJECT_DOMAIN,
        "endpoints": ENDPOINTS,
        "required": REQUIRED_ENDPOINTS,
    }
