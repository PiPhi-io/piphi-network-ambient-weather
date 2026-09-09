from __future__ import annotations
import os
from typing import Any
from fastapi import HTTPException
from piphi_runtime_kit_python import AutomationRegistry,SQLiteAutomationIdempotencyStore,build_local_event_record,build_runtime_identity,create_runtime_starter
from .contract import CAPABILITIES,COMMANDS
from .provider import AmbientWeatherClient
from .schemas import DeviceConfig
from .settings import INTEGRATION_ID,INTEGRATION_NAME,INTEGRATION_VERSION
starter=create_runtime_starter(integration_id=INTEGRATION_ID,integration_name=INTEGRATION_NAME,version=INTEGRATION_VERSION)
runtime,registry,telemetry,config_sync=starter.runtime,starter.registry,starter.telemetry_client,starter.config_sync
automations=AutomationRegistry(idempotency_store=SQLiteAutomationIdempotencyStore(os.getenv("PIPHI_AUTOMATION_LEDGER_PATH","./data/automation-actions.sqlite3")))
capabilities,commands=CAPABILITIES,COMMANDS
def make_entry(config:DeviceConfig)->dict[str,Any]:
    identity=build_runtime_identity(config,integration_id=INTEGRATION_ID)
    return {**identity,"host":config.host,"alias":config.alias,"config":config.model_dump(),"devices":[]}
def append_runtime_event(event_type:str,device:dict[str,Any],payload:dict[str,Any]|None=None)->dict[str,Any]:
    event=build_local_event_record(event_type=event_type,device=device,payload=payload or {},source=INTEGRATION_ID,severity="info");registry.append_event(event);return event
def get_entry_or_404(config_id:str)->dict[str,Any]:
    entry=registry.get(config_id)
    if entry is None:raise HTTPException(status_code=404,detail=f"unknown config_id={config_id}")
    return entry
async def apply_config(config:DeviceConfig)->None:
    entry=make_entry(config);registry.set(config.id,entry);registry.update_state(config.id,{"connected":False,"station_count":0},device_id=entry["device_id"]);append_runtime_event("runtime.config.applied",entry,{"account_id":config.account_id})
async def remove_config(config_id:str)->bool:
    entry=registry.remove(config_id)
    if entry is None:return False
    append_runtime_event("runtime.config.removed",entry,{"account_id":entry.get("host")});return True
async def refresh_entry(config_id:str)->dict[str,Any]:
    entry=get_entry_or_404(config_id);config=DeviceConfig.model_validate(entry["config"])
    client=AmbientWeatherClient(application_key=config.application_key.get_secret_value(),api_key=config.api_key.get_secret_value(),base_url=config.base_url or "https://api.ambientweather.net/v1")
    try:devices=await client.devices()
    finally:await client.close()
    entry["devices"]=devices;state={"connected":True,"station_count":len(devices),"stations":devices};registry.update_state(config_id,state,device_id=entry["device_id"]);append_runtime_event("weather.observation_refreshed",entry,{"station_count":len(devices)});return state
@automations.action("refresh",label="Refresh Ambient Weather stations")
async def refresh_action(request):
    target=request.target if isinstance(request.target,dict) else {}
    return await refresh_entry(str(request.config_id or target.get("config_id") or request.device_id or ""))
