from __future__ import annotations

import httpx
import pytest

from piphi_network_ambient_weather.provider import AmbientWeatherClient, AmbientWeatherError, normalize_device, normalize_observation


def test_normalize_device_and_optional_sensors() -> None:
    device = normalize_device({"macAddress":"AA:BB:CC:DD:EE:FF","info":{"name":"Backyard","coords":{"coords":{"lat":40,"lon":-75}}},"lastData":{"dateutc":123,"tempf":72.5,"humidity":44,"pm25":8.2,"lightning_num":2,"soilhum1":31,"battout":1}})
    assert device["id"] == "aabbccddeeff"
    assert device["coordinates"] == {"latitude":40.0,"longitude":-75.0}
    assert device["last_observation"]["temperature_f"] == 72.5
    assert device["last_observation"]["temperature_c"] == 22.5
    assert device["last_observation"]["soil_moisture_1_percent"] == 31
    assert device["last_observation"]["outdoor_battery_ok"] is True


def test_normalize_does_not_invent_absent_model_capabilities() -> None:
    assert normalize_observation({"tempf":70}) == {"temperature_f":70,"temperature_c":21.111,"connected":True}


@pytest.mark.anyio
async def test_devices_uses_both_keys_without_leaking_them() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["applicationKey"] == "app-secret"
        assert request.url.params["apiKey"] == "user-secret"
        return httpx.Response(200, json=[{"macAddress":"AA:BB","lastData":{"tempf":70}}])
    client = AmbientWeatherClient(application_key="app-secret", api_key="user-secret", transport=httpx.MockTransport(handler))
    try:
        devices = await client.devices()
    finally:
        await client.close()
    assert "secret" not in repr(devices)


@pytest.mark.anyio
async def test_history_limit_fails_closed() -> None:
    client = AmbientWeatherClient(application_key="a", api_key="b")
    try:
        with pytest.raises(ValueError, match="288"):
            await client.history("AA", limit=289)
    finally:
        await client.close()


@pytest.mark.anyio
async def test_rate_limit_is_actionable() -> None:
    client = AmbientWeatherClient(application_key="a", api_key="b", transport=httpx.MockTransport(lambda _: httpx.Response(429)))
    try:
        with pytest.raises(AmbientWeatherError, match="rate limit"):
            await client.devices()
    finally:
        await client.close()
