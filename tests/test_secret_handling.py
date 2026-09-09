from __future__ import annotations
from piphi_network_ambient_weather.routes.runtime import _public_entries
from piphi_network_ambient_weather.state import registry
def test_runtime_state_redacts_keys()->None:
    registry.entries["secret-test"]={"config":{"api_key":"user-secret","application_key":"app-secret","account_id":"safe"}}
    try:
        public=_public_entries()["secret-test"];assert public["config"]["api_key"]=="***";assert "secret" not in repr(public)
    finally:registry.entries.pop("secret-test",None)
