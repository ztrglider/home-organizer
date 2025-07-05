"""Sensor platform for Room Chore Picker."""

from __future__ import annotations

from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, SENSOR_NAME


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    picker = hass.data[DOMAIN]
    sensor = RoomPickerSensor(picker)
    async_add_entities([sensor])

    @callback
    def handle_update(event):
        sensor.async_write_ha_state()

    hass.bus.async_listen(f"{DOMAIN}_updated", handle_update)


class RoomPickerSensor(Entity):
    """Representation of the recommended room sensor."""

    _attr_should_poll = False
    _attr_name = SENSOR_NAME
    _attr_unique_id = f"{DOMAIN}_weekly_room_target"

    def __init__(self, picker) -> None:
        self.picker = picker

    @property
    def state(self):
        return self.picker.recommended_room
