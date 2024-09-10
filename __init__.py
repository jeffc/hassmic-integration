"""The hassmic integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, Entity

from . import const
from .hassmic import HassMic


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hassmic from a config entry."""

    # Create a HassMic instance and keep it in the runtime_data of the
    # ConfigEntry, so it can be accessed from anywhere in the entry.
    entry.runtime_data = HassMic(hass, entry)

    # TODO Optionally validate config entry options before setting up platform

    await hass.config_entries.async_forward_entry_setups(entry, const.PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


def init_entity(entity: Entity, key: str, config_entry: ConfigEntry) -> str:
    """Initialize the deviceinfo and other metadata for an entity.

    "key" is the unique name within this device for the given entity (ie "wake" or
    "tts").
    """
    unique_id = config_entry.entry_id
    entity.unique_id = f"{unique_id}-{key}"
    entity.name = config_entry.title + " " + key.upper().replace("_", " ")
    entity.icon = const.PROPERTIES_META_INFO.get(key, {}).get(
        "icon", "mdi:numeric-0"
    )
    entity.device_info = DeviceInfo(
        name=config_entry.title,
        identifiers={(const.DOMAIN, unique_id)},
    )


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    await entry.runtime_data.stop()
    return await hass.config_entries.async_unload_platforms(entry, const.PLATFORMS)
