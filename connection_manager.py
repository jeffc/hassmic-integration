"""Manages the network connection for an entry (device)."""

import asyncio
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class ConnectionManager:
  """Manages a connection."""

  def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    self._hass = hass
    self._config_entry = config_entry

    self._socket_reader = None
    self._socket_writer = None

    self._host = config_entry.options.get("hostname")
    self._port = config_entry.options.get("port")

    self._is_connected = False
    self._should_close = False

    _LOGGER.info(f"Starting network tasks for {self._host}:{self._port}")
    hass.async_add_executor_job(asyncio.run, self.do_net())
    
  async def reconnect(self) -> None:
    if self._is_connected:
      _LOGGER.debug(f"Already connected to {self._host}:{self._port}, reconnecting")
      await self.destroy_socket()

    try:
      _LOGGER.debug(f"Trying connection to {self._host}:{self._port}")
      self._socket_reader, self._socket_writer = (
          await asyncio.open_connection(self._host, self._port))
      self._is_connected = True
      _LOGGER.debug(f"Connected to {self._host}:{self._port}")
    except Exception as e:
      self._is_connected = False
      _LOGGER.error(
        f"Encountered an error trying to connect to {self._host}:{self._port}: {e!r}")

  async def destroy_socket(self):
    """Actually kills the connection.

    Outside callers should call close() instead."""
    self._is_connected = False
    self._socket_writer.close() # writer controls the underlying socket
    await self._socket_writer.wait_closed()

  async def close(self):
    """Request close of this conn manager."""
    _LOGGER.debug("Closing conn manager")
    self._should_close = True
  
  async def do_net(self):
    while not self._should_close:
      is_eof = False
      await self.reconnect()
      try:
        while self._is_connected and not is_eof and not self._should_close:
          b = await self._socket_reader.readline()
          if b == b"":
            _LOGGER.debug("Got EOF")
            is_eof = True
      except ConnectionResetError:
        _LOGGER.warn(f"Connection to {self._host}:{self._port} lost")
      except Exception as e:
        _LOGGER.error(f"Unexpected exception: {e!r}")

      _LOGGER.warn(f"Disconnected from {self._host}:{self._port}; will reconnect")
      await asyncio.sleep(2)

    _LOGGER.info(f"Shutting down connection to {self._host}:{self._port}")
    self.destroy_socket()
