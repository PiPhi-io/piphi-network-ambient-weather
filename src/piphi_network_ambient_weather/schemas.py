from __future__ import annotations
from pydantic import Field, SecretStr
from piphi_runtime_kit_python import RuntimeConfig

class DeviceConfig(RuntimeConfig):
    account_id:str="ambient-weather"
    alias:str|None=None
    application_key:SecretStr
    api_key:SecretStr
    base_url:str|None=None
    poll_interval_seconds:int=Field(default=300,ge=60)
    @property
    def host(self)->str:return self.account_id
