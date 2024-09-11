"""Sensor platform for hassmic integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const, init_entity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize hassmic config entry."""
    async_add_entities(
        [hassmicSensorEntity(config_entry, key) for key in const.SENSORS_ALL]
    )


class hassmicSensorEntity(SensorEntity):
    """hassmic Sensor."""

    def __init__(self, config_entry: ConfigEntry, key: str) -> None:
        """Initialize hassmic Sensor."""
        super().__init__()
        init_entity(self, key, config_entry)
