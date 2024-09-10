"""The hassmic integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import const

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hassmic from a config entry."""
    # TODO Optionally store an object for your platforms to access
    # entry.runtime_data = ...

    # TODO Optionally validate config entry options before setting up platform

    await hass.config_entries.async_forward_entry_setups(entry, (Platform.SENSOR,))

    # TODO Remove if the integration does not have an options flow
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True

def init_entity(entity: Entity, key: str, config_entry: ConfigEntry) -> str:
  """Initializes the deviceinfo and other metadata for an entity.

  "key" is the unique name within this device for the given entity (ie "wake" or
  "tts").
  """
  unique_id = config_entry.entry_id
  entity._attr_unique_id = f"{unique_id}-{key}"
  entity._attr_name = config_entry.title + " " + key.upper().replace("_", " ")
  entity._attr_icon = const.PROPERTIES_META_INFO.get(key, {}).get("icon", "mdi:numeric-0")
  entity._attr_device_info = DeviceInfo(
      name=config_entry.title,
      identifiers={(const.DOMAIN, unique_id)},
  )


# TODO Remove if the integration does not have an options flow
async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, (Platform.SENSOR,))
