"""Constants for the hassmic integration."""

from homeassistant.const import Platform

# The name of this integration
DOMAIN = "hassmic"

# The platforms this integration provides
PLATFORMS = [
    Platform.SENSOR,
]

# An information struct for the generated properties (read-only entities) that
# this integration provides
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
    },
}

# A list of the sensors provided by each instance of this integration
SENSORS_ALL = [
    "wake",
    "stt",
    "intent",
    "tts",
]
