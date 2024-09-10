import asyncio
import enum
import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .connection_manager import ConnectionManager
from .exceptions import BadMessageException

MAX_CHUNK_SIZE = 8192
MAX_JSON_SIZE = 1024

EXTRA_MSG_TIMEOUT_SECS = 0.5

MESSAGE_TYPE_AUDIO_CHUNK = "audio-chunk"

_LOGGER = logging.getLogger(__name__)



class Message:
    """Defines a message type for the "Cheyenne" protocol."""

    class MessageType(enum.Enum):
        """The list of possible message types."""

        UNKNOWN = None
        AUDIO_CHUNK = "audio-chunk"

    def __init__(self, **kwargs):
        self.message_type = MessageType.UNKNOWN
        try:
            self.message_type = MessageType(kwargs.get("message_type", None))
        except ValueError:
            pass
        self.data = kwargs.get("data", {})
        self.payload = kwargs.get("payload", b"")

    def __repr__(self):
        return (
            f"Message ({self.message_type.name}): "
            f"{self.data!r} "
            f"(payload {len(self.payload)} bytes)"
        )


class HassMic:
    """Handles interface between the HassMic app and home assistant."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the instance."""

        self._hass = hass
        self._configentry = entry

        self._connection_manager = ConnectionManager(
            host=entry.options.get("hostname"),
            port=entry.options.get("port"),
            recv_fn=self.recv_message,
        )

        #hass.async_add_executor_job(asyncio.run, self._connection_manager.do_net())
        hass.async_create_background_task(self._connection_manager.do_net(), name="hassmic_connection")

    async def stop(self):
      """Shuts down instance."""
      await self._connection_manager.close()



    async def recv_message(self, reader):
        """Reads a message from the stream, or None if the stream is closed."""

        recv = await reader.readline()
        while recv == b"\n":  # skip blank lines if we're expecting JSON
            recv = await reader.readline()

        if recv == b"":
            return None

        msg = {}
        try:
            msg = json.loads(recv.decode("utf-8"))
        except UnicodeError:
            raise BadMessageException("Couldn't decode message")
        except json.JSONDecodeError:
            raise BadMessageException(f"Failed to decode JSON: '{recv}'")

        if "type" not in msg:
            raise BadMessageException(f"Field 'type' not in msg: '{msg};")

        extra_data = {}
        payload_bytes = b""

        if msg.get("data") is None:
            msg["data"] = {}

        if (data_length := msg.get("data_length", -1)) > 0:
            _LOGGER.debug("waiting for extra data")
            try:
                async with asyncio.timeout(EXTRA_MSG_TIMEOUT_SECS):
                    extra_data = await reader.readexactly(data_length)
                    try:
                        d = json.loads(recv.decode("utf-8"))
                        msg["data"] |= d
                    except UnicodeError:
                        raise BadMessageException("Couldn't decode extra data message")
                    except json.JSONDecodeError:
                        raise BadMessageException(
                            f"Failed to decode JSON for extra data: '{msg}'"
                        )
            except TimeoutError:
                raise BadMessageException("Timed out waiting for extra data")

        if (payload_length := msg.get("payload_length", -1)) > 0:
            _LOGGER.debug("waiting for payload")
            try:
                async with asyncio.timeout(EXTRA_MSG_TIMEOUT_SECS):
                    payload_bytes = await reader.readexactly(payload_length)
            except TimeoutError:
                raise BadMessageException("Timed out waiting for payload")

        msg["payload"] = payload_bytes

        return Message(
            message_type=msg["type"],
            data=msg["data"],
            payload=msg["payload"],
        )
