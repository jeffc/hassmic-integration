"""Main class for hassmic."""

import asyncio
import contextlib
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


class MessageType(enum.Enum):
    """The list of possible message types."""

    UNKNOWN = None
    AUDIO_CHUNK = "audio-chunk"


class Message:
    """Defines a message type for the "Cheyenne" protocol."""

    def __init__(self, **kwargs):
        """Create a new Message with the given params."""
        self.message_type = MessageType.UNKNOWN

        with contextlib.suppress(ValueError):
            self.message_type = MessageType(kwargs.get("message_type", None))

        self.data = kwargs.get("data", {})
        self.payload = kwargs.get("payload", b"")

    def __repr__(self):
        """Stringify the message."""
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

        self._host = entry.options.get("hostname")
        self._port = entry.options.get("port")

        self._connection_manager = ConnectionManager(
            host=self._host,
            port=self._port,
            recv_fn=self.handle_message,
        )

        hass.async_create_background_task(
            self._connection_manager.do_net(), name="hassmic_connection"
        )

    async def stop(self):
        """Shut down instance."""
        await self._connection_manager.close()

    async def handle_message(self, reader) -> Message:
        """Wrap handle_message and dispatches recieved messages appropriately."""

        m = self.recv_message(reader)
        if m is None:
            return None

        match m.type:
            case MessageType.UNKNOWN:
                _LOGGER.warning(
                    "Got an unknown message from " "%s:%d. Ignoring it.",
                    self._host,
                    self._port,
                )

            case MessageType.AUDIO_CHUNK:
                # handle audio data
                rate = m.data.get("rate")
                width = m.data.get("width")
                channels = m.data.get("channels")

            case _:
                _LOGGER.error("Got unhandled (but known) message type %s", m.type.name)

        return m

    async def recv_message(self, reader) -> Message:
        """Read a message from the stream, or None if the stream is closed."""

        recv = await reader.readline()
        while recv == b"\n":  # skip blank lines if we're expecting JSON
            recv = await reader.readline()

        if recv == b"":
            return None

        msg = {}
        try:
            msg = json.loads(recv.decode("utf-8"))
        except UnicodeError as err:
            raise BadMessageException("Couldn't decode message") from err
        except json.JSONDecodeError as err:
            raise BadMessageException("Failed to decode JSON: '%s'", recv) from err

        if "type" not in msg:
            raise BadMessageException("Field 'type' not in msg: '%s'", msg)

        payload_bytes = b""

        if msg.get("data") is None:
            msg["data"] = {}

        if (data_length := msg.get("data_length", -1)) > 0:
            _LOGGER.debug("waiting for extra data")
            try:
                async with asyncio.timeout(EXTRA_MSG_TIMEOUT_SECS):
                    extra_data = await reader.readexactly(data_length)
                    try:
                        d = json.loads(extra_data.decode("utf-8"))
                        msg["data"] |= d
                    except UnicodeError as err:
                        raise BadMessageException(
                            "Couldn't decode extra data message"
                        ) from err
                    except json.JSONDecodeError as err:
                        raise BadMessageException(
                            "Failed to decode JSON for extra data: '%s'", msg
                        ) from err
            except TimeoutError as err:
                raise BadMessageException("Timed out waiting for extra data") from err

        if (payload_length := msg.get("payload_length", -1)) > 0:
            _LOGGER.debug("waiting for payload")
            try:
                async with asyncio.timeout(EXTRA_MSG_TIMEOUT_SECS):
                    payload_bytes = await reader.readexactly(payload_length)
            except TimeoutError as err:
                raise BadMessageException("Timed out waiting for payload") from err

        return Message(
            message_type=msg["type"],
            data=msg["data"],
            payload=payload_bytes,
        )
