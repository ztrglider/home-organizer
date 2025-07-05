"""Room Chore Picker integration."""

from __future__ import annotations

import random
from datetime import timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import storage
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.util import dt as dt_util

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION, SERVICE_SHUFFLE


class RoomChorePicker:
    """Class handling room selection and storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = storage.Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.recommended_room: str | None = None
        self._remove_listener = None

    async def async_load(self) -> None:
        data = await self.store.async_load() or {}
        self.recommended_room = data.get("recommended_room")

    async def async_save(self) -> None:
        await self.store.async_save({"recommended_room": self.recommended_room})

    async def async_shuffle(self, *_: ServiceCall) -> None:
        registry = await async_get_area_registry(self.hass)
        areas = [a.name for a in registry.async_list_areas()]
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
        next_time = dt_util.start_of_local_day(now + timedelta(days=days_ahead))

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
    picker = RoomChorePicker(hass)
    await picker.async_start()

    async def handle_shuffle(call: ServiceCall) -> None:
        await picker.async_shuffle(call)

    hass.services.async_register(DOMAIN, SERVICE_SHUFFLE, handle_shuffle)
    hass.data[DOMAIN] = picker
    async_load_platform(hass, "sensor", DOMAIN, {}, config)
    return True
