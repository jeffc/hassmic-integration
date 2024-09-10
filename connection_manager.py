"""Manages the network connection for an entry (device)."""

import asyncio
import logging

from .exceptions import BadMessageException

_LOGGER = logging.getLogger(__name__)

# How many bad messages in a row should cause us to drop the connection and
# reconnect
MAX_CONSECUTIVE_BAD_MESSAGES = 5


class ConnectionManager:
    """Manages a connection, including reconnects.

    Accepts a callback (`recv_fn`) which accepts a stream and reads messages
    from it.
    """

    def __init__(
        self,
        host: str,
        port: int,
        recv_fn,  # unclear how to type-hint this
    ) -> None:
        """Constructor."""
        self._socket_reader = None
        self._socket_writer = None

        self._host = host
        self._port = port

        self._is_connected = False
        self._should_close = False

        # set a callback that processes the connection
        self._recv_fn = recv_fn

    async def reconnect(self) -> None:
        if self._is_connected:
            _LOGGER.debug(
                f"Already connected to {self._host}:{self._port}, reconnecting"
            )
            await self.destroy_socket()

        try:
            _LOGGER.debug(f"Trying connection to {self._host}:{self._port}")
            self._socket_reader, self._socket_writer = await asyncio.open_connection(
                self._host, self._port
            )
            self._is_connected = True
            _LOGGER.debug(f"Connected to {self._host}:{self._port}")
        except Exception as e:
            self._is_connected = False
            _LOGGER.error(
                f"Encountered an error trying to connect to {self._host}:{self._port}: {e!r}"
            )

    async def destroy_socket(self):
        """Actually kills the connection.

        Outside callers should call close() instead.
        """
        self._is_connected = False
        if self._socket_writer is None:
          # no socket to destroy
          return

        if not self._socket_writer.is_closing():
            self._socket_writer.close()  # writer controls the underlying socket
        try:
            await self._socket_writer.wait_closed()
        except ConnectionError:
            # ignore connection errors when we're trying to close the connection
            # anyways
            pass

    async def close(self):
        """Request close of this conn manager."""
        _LOGGER.debug("Closing conn manager")
        self._should_close = True

    async def do_net(self):
        _LOGGER.info(f"Starting network tasks for {self._host}:{self._port}")
        while not self._should_close:
            is_eof = False
            await self.reconnect()
            bad_messages = 0  # track consecutive bad messages
            try:
                while self._is_connected and not is_eof and not self._should_close:
                    try:
                        msg = await self._recv_fn(self._socket_reader)
                        if msg is None:
                            _LOGGER.debug("Got EOF")
                            is_eof = True
                    except BadMessageException as e:
                        _LOGGER.error(f"{e!r}")
                        bad_messages += 1
                        if bad_messages >= MAX_CONSECUTIVE_BAD_MESSAGES:
                            _LOGGER.error(
                                "Reached threshold for consecutive bad messages; reconnecting"
                            )
                            await self.reconnect()
                            bad_messages = 0
                        continue

                    bad_messages = 0
            except ConnectionResetError:
                _LOGGER.warning(f"Connection to {self._host}:{self._port} lost")
            except Exception as e:
                _LOGGER.error(f"Unexpected exception: {e!r}")

            _LOGGER.warning(f"Disconnected from {self._host}:{self._port}; will reconnect")
            await asyncio.sleep(2)

        _LOGGER.info(f"Shutting down connection to {self._host}:{self._port}")
        await self.destroy_socket()
