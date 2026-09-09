from __future__ import annotations
import json
from pathlib import Path
from piphi_network_ambient_weather.contract import CAPABILITIES,COMMANDS
ROOT=Path(__file__).parents[1]
def test_catalog_ids_are_unique_and_implemented_entries_are_advertised()->None:
    rows=json.loads((ROOT/"capability-catalog.json").read_text())["capabilities"];ids=[row["id"] for row in rows];assert len(ids)==len(set(ids));implemented={row["id"] for row in rows if row["status"]=="implemented"};assert implemented<=set(CAPABILITIES);assert {row["id"] for row in rows if row["kind"]=="action" and row["status"]=="implemented"}==set(COMMANDS)
def test_unavailable_catalog_entries_are_not_advertised()->None:
    rows=json.loads((ROOT/"capability-catalog.json").read_text())["capabilities"];unavailable={row["id"] for row in rows if row["status"]!="implemented"};assert unavailable.isdisjoint(CAPABILITIES)
