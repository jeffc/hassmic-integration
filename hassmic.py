import asyncio
import base64
import json
import sys
import logging

MAX_CHUNK_SIZE=8192
MAX_JSON_SIZE=1024

EXTRA_MSG_TIMEOUT_SECS = 0.5

MESSAGE_TYPE_AUDIO_CHUNK = "audio-chunk"

_LOGGER = logging.getLogger(__name__)

class BadMessageException(Exception):
  pass

async def read_message(reader):
  """Returns a new message, or None if the stream is closed."""
  recv = await reader.readline()
  while recv == b"\n": # skip blank lines if we're expecting JSON
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
          raise BadMessageException(f"Failed to decode JSON for extra data: '{msg}'")
    except asyncio.TimeoutError:
      raise BadMessageException("Timed out waiting for extra data")

  if (payload_length := msg.get("payload_length", -1)) > 0:
    _LOGGER.debug("waiting for payload")
    try:
      async with asyncio.timeout(EXTRA_MSG_TIMEOUT_SECS):
        payload_bytes = await reader.readexactly(payload_length)
    except asyncio.TimeoutError:
      raise BadMessageException("Timed out waiting for payload")

  msg["payload"] = payload_bytes

  return msg
