"""Constants for the hassmic integration."""

from homeassistant.const import Platform

DOMAIN = "hassmic"

PLATFORMS = [Platform.SENSOR, ]

PROPERTIES_META_INFO = {
    "mic": {
      "icon": "mdi:microphone",
    },
    "wake": {
      "icon": "mdi:chat-alert-outline",
    },
    "stt": {
      "icon": "mdi:ear-hearing",
    },
    "intent": {
      "icon": "mdi:brain",
    },
    "tts": {
      "icon": "mdi:speaker-message",
    }
  }

SENSORS_ALL = [
    "wake",
    "stt",
    "intent",
    "tts",
]

