"""Constants for the hassmic integration."""

DOMAIN = "hassmic"

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

