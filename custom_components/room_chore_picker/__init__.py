"""Room Chore Picker integration."""

from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import storage
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.util import dt as dt_util

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION, SERVICE_SHUFFLE


def _normalize_area_filter(raw: Any) -> set[str] | None:
    """Return a lower-cased set of area names from config input."""

    if raw is None:
        return None

    if isinstance(raw, str):
        candidates = [raw]
    else:
        try:
            candidates = list(raw)
        except TypeError:
            return None

    normalized = {
        candidate.casefold()
        for candidate in candidates
        if isinstance(candidate, str) and candidate.strip()
    }

    return normalized


class RoomChorePicker:
    """Class handling room selection and storage."""

    def __init__(
        self,
        hass: HomeAssistant,
        include_areas: set[str] | None = None,
        exclude_areas: set[str] | None = None,
    ) -> None:
        self.hass = hass
        self.store = storage.Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.recommended_room: str | None = None
        self._remove_listener = None
        self._include_areas = include_areas.copy() if include_areas is not None else None
        self._exclude_areas = exclude_areas.copy() if exclude_areas else set()

    async def async_load(self) -> None:
        data = await self.store.async_load() or {}
        self.recommended_room = data.get("recommended_room")

    async def async_save(self) -> None:
        await self.store.async_save({"recommended_room": self.recommended_room})

    async def async_shuffle(self, *_: ServiceCall) -> None:
        registry = async_get_area_registry(self.hass)
        areas = [a.name for a in registry.async_list_areas()]

        if self._include_areas is not None:
            areas = [
                area
                for area in areas
                if area.casefold() in self._include_areas
            ]

        if self._exclude_areas:
            areas = [
                area
                for area in areas
                if area.casefold() not in self._exclude_areas
            ]
        if not areas:
            self.recommended_room = None
        else:
            choices = [a for a in areas if a != self.recommended_room]
            if not choices:
                choices = areas
            self.recommended_room = random.choice(choices)
        await self.async_save()
        self.hass.bus.async_fire(f"{DOMAIN}_updated")

    async def _schedule_next(self) -> None:
        now = dt_util.utcnow()
        days_ahead = (5 - now.weekday()) % 7  # Saturday
        next_time_local = dt_util.start_of_local_day(now + timedelta(days=days_ahead))
        next_time = dt_util.as_utc(next_time_local)

        async def _run(now):
            await self.async_shuffle()
            await self._schedule_next()

        self._remove_listener = async_track_point_in_utc_time(
            self.hass, _run, next_time
        )

    async def async_start(self) -> None:
        await self.async_load()
        await self._schedule_next()

    async def async_stop(self) -> None:
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    domain_config = config.get(DOMAIN, {})

    if isinstance(domain_config, list):
        domain_config = domain_config[0] if domain_config else {}

    include_filter = _normalize_area_filter(domain_config.get("include_areas"))
    exclude_filter = _normalize_area_filter(domain_config.get("exclude_areas")) or set()

    picker = RoomChorePicker(hass, include_filter, exclude_filter)
    await picker.async_start()

    async def handle_shuffle(call: ServiceCall) -> None:
        await picker.async_shuffle(call)

    hass.services.async_register(DOMAIN, SERVICE_SHUFFLE, handle_shuffle)
    hass.data[DOMAIN] = picker
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    return True
