import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from datetime import datetime


def _ensure_fake_homeassistant_modules() -> None:
    """Inject lightweight stubs so the integration module can be imported."""

    if "homeassistant" in sys.modules:
        return

    ha_module = ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha_module

    core = ModuleType("homeassistant.core")
    core.HomeAssistant = object
    core.ServiceCall = object
    sys.modules["homeassistant.core"] = core

    helpers = ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = helpers

    storage = ModuleType("homeassistant.helpers.storage")

    class _DummyStore:
        async def async_load(self):
            return {}

        async def async_save(self, data):  # pragma: no cover - simple stub
            return None

    storage.Store = _DummyStore
    sys.modules["homeassistant.helpers.storage"] = storage

    area_registry = ModuleType("homeassistant.helpers.area_registry")

    def _not_implemented(*args, **kwargs):  # pragma: no cover - guard stub
        raise NotImplementedError

    area_registry.async_get = _not_implemented
    sys.modules["homeassistant.helpers.area_registry"] = area_registry

    event = ModuleType("homeassistant.helpers.event")
    event.async_track_point_in_utc_time = lambda *args, **kwargs: lambda: None
    sys.modules["homeassistant.helpers.event"] = event

    typing_mod = ModuleType("homeassistant.helpers.typing")
    typing_mod.ConfigType = dict
    sys.modules["homeassistant.helpers.typing"] = typing_mod

    discovery = ModuleType("homeassistant.helpers.discovery")
    discovery.async_load_platform = lambda *args, **kwargs: None
    sys.modules["homeassistant.helpers.discovery"] = discovery

    util = ModuleType("homeassistant.util")
    dt_helpers = SimpleNamespace(
        utcnow=datetime.utcnow,
        start_of_local_day=lambda value: value.replace(
            hour=0, minute=0, second=0, microsecond=0
        ),
        as_utc=lambda value: value,
    )
    util.dt = dt_helpers
    sys.modules["homeassistant.util"] = util


_ensure_fake_homeassistant_modules()

sys.path.append(str(Path(__file__).resolve().parents[1]))

from custom_components.room_chore_picker.__init__ import (
    _filter_areas,
    _normalize_area_filter,
    _select_recommended_room,
)


def test_normalize_area_filter_accepts_iterables():
    assert _normalize_area_filter("Kitchen") == {"kitchen"}
    assert _normalize_area_filter(["Kitchen", "Living Room"]) == {
        "kitchen",
        "living room",
    }
    assert _normalize_area_filter({"Kitchen", "Office"}) == {"kitchen", "office"}


def test_normalize_area_filter_ignores_invalid_values():
    assert _normalize_area_filter(None) is None
    assert _normalize_area_filter(5) is None
    assert _normalize_area_filter(["Kitchen", "", None, 42]) == {"kitchen"}


def test_filter_areas_respects_include_and_exclude():
    areas = ["Kitchen", "Living Room", "Office", "Backyard"]
    include = {"kitchen", "office"}
    exclude = {"office"}

    assert _filter_areas(areas, include, exclude) == ["Kitchen"]


def test_filter_areas_without_include_only_uses_exclude():
    areas = ["Kitchen", "Living Room", "Office"]
    include = None
    exclude = {"living room"}

    assert _filter_areas(areas, include, exclude) == ["Kitchen", "Office"]


def test_select_recommended_room_avoids_immediate_repeats():
    areas = ["Kitchen", "Living Room", "Office"]
    current = "Kitchen"

    chosen = _select_recommended_room(areas, current, lambda pool: pool[0])

    assert chosen == "Living Room"


def test_select_recommended_room_handles_single_choice():
    areas = ["Kitchen"]
    current = "Kitchen"

    chosen = _select_recommended_room(areas, current, lambda pool: pool[0])

    assert chosen == "Kitchen"


def test_select_recommended_room_returns_none_for_empty_pool():
    assert _select_recommended_room([], None, lambda pool: pool[0]) is None
