from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from ..contract import FALLBACK_ENTITY
from ..state import capabilities,commands,registry
router=APIRouter(tags=["entities"])
@router.get("/entities")
async def entities()->dict[str,Any]:
    result=[]
    for entry in registry.entries.values():
        for device in entry.get("devices",[]):
            observation=device.get("last_observation",{});supported=[key for key in observation if key in capabilities]+["refresh"]
            result.append({"id":device["id"],"name":device["name"],"config_id":entry["config_id"],"device_id":device["id"],"entity_type":"weather_station","capabilities":supported,"available_commands":[{"id":"refresh","label":"Refresh stations","kind":"action"}],"dashboard":{"allowed_widgets":["weather-station","tile","stat"],"default_widget":"weather-station"}})
    return {"entities":result or [FALLBACK_ENTITY],"capabilities":capabilities,"commands":commands}
