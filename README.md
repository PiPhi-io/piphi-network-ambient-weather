# PiPhi Ambient Weather

AmbientWeather.net integration for station discovery, current observations, model-specific sensors, canonical SI conversions, and bounded REST history. Authentication uses separate application and user API keys; both are treated as secrets and redacted from runtime state.

The official API is read-only. Realtime Socket.IO delivery and transition events are inventoried for a later release and are not advertised by version 0.1.

```bash
pdm install -G dev
pdm run pytest
pdm run uvicorn piphi_network_ambient_weather.main:app --port 8090
```

See `capability-catalog.json` for the complete coverage ledger.
