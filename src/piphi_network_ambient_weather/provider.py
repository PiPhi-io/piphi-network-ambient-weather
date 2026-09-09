from __future__ import annotations

from typing import Any

import httpx


DEFAULT_BASE_URL = "https://api.ambientweather.net/v1"


class AmbientWeatherError(RuntimeError):
    pass


class AmbientWeatherClient:
    def __init__(self, *, application_key: str, api_key: str, base_url: str = DEFAULT_BASE_URL, transport: httpx.AsyncBaseTransport | None = None) -> None:
        if not application_key or not api_key:
            raise ValueError("application_key and api_key are required")
        self._auth = {"applicationKey": application_key, "apiKey": api_key}
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=15.0, transport=transport)

    async def close(self) -> None:
        await self._client.aclose()

    async def devices(self) -> list[dict[str, Any]]:
        response = await self._client.get("/devices", params=self._auth)
        _raise_for_status(response)
        payload = response.json()
        if not isinstance(payload, list):
            raise AmbientWeatherError("Ambient Weather devices response is not a list")
        return [normalize_device(item) for item in payload]

    async def history(self, mac_address: str, *, limit: int = 288, end_date: int | None = None) -> list[dict[str, Any]]:
        if not 1 <= limit <= 288:
            raise ValueError("limit must be between 1 and 288")
        params: dict[str, Any] = {**self._auth, "limit": limit}
        if end_date is not None:
            params["endDate"] = end_date
        response = await self._client.get(f"/devices/{mac_address}", params=params)
        _raise_for_status(response)
        payload = response.json()
        if not isinstance(payload, list):
            raise AmbientWeatherError("Ambient Weather history response is not a list")
        return [normalize_observation(item) for item in payload]


def normalize_device(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AmbientWeatherError("Ambient Weather device is not an object")
    mac = str(payload.get("macAddress") or "").strip().upper()
    if not mac:
        raise AmbientWeatherError("Ambient Weather device is missing macAddress")
    info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
    return {
        "id": mac.replace(":", "").lower(),
        "mac_address": mac,
        "name": info.get("name") or info.get("location") or f"Weather station {mac[-5:]}",
        "location": info.get("location"),
        "coordinates": _safe_coordinates(info),
        "last_observation": normalize_observation(payload.get("lastData", {})),
    }


def normalize_observation(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AmbientWeatherError("Ambient Weather observation is not an object")
    field_map = {
        "dateutc":"observed_at_ms", "tempf":"temperature_f", "humidity":"humidity_percent", "baromrelin":"pressure_relative_inhg", "baromabsin":"pressure_absolute_inhg",
        "windspeedmph":"wind_speed_mph", "windgustmph":"wind_gust_mph", "maxdailygust":"wind_gust_daily_max_mph", "winddir":"wind_direction_deg",
        "hourlyrainin":"rain_hourly_in", "dailyrainin":"rain_daily_in", "weeklyrainin":"rain_weekly_in", "monthlyrainin":"rain_monthly_in", "yearlyrainin":"rain_yearly_in",
        "solarradiation":"solar_radiation_wm2", "uv":"uv_index", "feelsLike":"feels_like_f", "dewPoint":"dew_point_f",
        "tempinf":"indoor_temperature_f", "humidityin":"indoor_humidity_percent", "pm25":"pm25_ugm3", "pm25_24h":"pm25_24h_ugm3",
        "aqi_pm25":"pm25_aqi", "aqi_pm25_24h":"pm25_aqi_24h", "lightning_distance":"lightning_distance_mi", "lightning_num":"lightning_count",
        "soilhum1":"soil_moisture_1_percent", "soilhum2":"soil_moisture_2_percent", "soilhum3":"soil_moisture_3_percent", "soilhum4":"soil_moisture_4_percent",
    }
    result = {target: payload[source] for source, target in field_map.items() if payload.get(source) is not None}
    if payload.get("tempf") is not None:
        result["temperature_c"] = round((float(payload["tempf"]) - 32) * 5 / 9, 3)
    if payload.get("baromrelin") is not None:
        result["pressure_hpa"] = round(float(payload["baromrelin"]) * 33.8638866667, 3)
    if payload.get("windspeedmph") is not None:
        result["wind_speed_mps"] = round(float(payload["windspeedmph"]) * 0.44704, 3)
    if payload.get("windgustmph") is not None:
        result["wind_gust_mps"] = round(float(payload["windgustmph"]) * 0.44704, 3)
    if payload.get("hourlyrainin") is not None:
        result["rain_mm"] = round(float(payload["hourlyrainin"]) * 25.4, 3)
    if payload.get("lightning_distance") is not None:
        result["lightning_distance_km"] = round(float(payload["lightning_distance"]) * 1.609344, 3)
    result["connected"] = bool(result)
    if payload.get("battout") is not None:
        result["outdoor_battery_ok"] = int(payload["battout"]) == 1
    if payload.get("batt_lightning") is not None:
        result["lightning_battery_ok"] = int(payload["batt_lightning"]) == 1
    for index in range(1, 11):
        key = f"batt{index}"
        if payload.get(key) is not None:
            result[f"sensor_{index}_battery_ok"] = int(payload[key]) == 1
    return result


def _safe_coordinates(info: dict[str, Any]) -> dict[str, float] | None:
    coords = info.get("coords")
    if isinstance(coords, dict) and isinstance(coords.get("coords"), dict):
        coords = coords["coords"]
    if not isinstance(coords, dict):
        return None
    lat, lon = coords.get("lat"), coords.get("lon")
    return {"latitude": float(lat), "longitude": float(lon)} if lat is not None and lon is not None else None


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == 429:
        raise AmbientWeatherError("Ambient Weather rate limit exceeded")
    if response.status_code in {401, 403}:
        raise AmbientWeatherError("Ambient Weather rejected the application or API key")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise AmbientWeatherError(f"Ambient Weather request failed with HTTP {response.status_code}") from exc
