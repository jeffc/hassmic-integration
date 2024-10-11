"""Defines a class to manage the assist pipeline."""

import asyncio
import logging

from homeassistant.components import assist_pipeline, stt
from homeassistant.components.assist_pipeline.error import WakeWordDetectionError
from homeassistant.components.assist_pipeline.pipeline import (
    PipelineEventCallback,
    PipelineStage,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

_LOGGER = logging.getLogger(__name__)

# Maximum number of chunks in the queue before dumping
QUEUE_MAX_CHUNKS = 2048

class QueueAsyncIterable:
    """Wrapper around an asyncio queue that provides AsyncIterable[bytes]."""

    def __init__(self, q: asyncio.Queue[bytes]):
        """Construct a new wrapper."""
        self._queue = q

    def __aiter__(self):
        """Complete the asynciterator signature."""
        return self

    async def __anext__(self) -> bytes:
        """Return the next chunk."""
        return await self._queue.get()


class PipelineManager:
    """Manages the connection to the assist pipeline."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry, event_callback: PipelineEventCallback):
        """Construct a new manager."""
        self._hass: HomeAssistant = hass
        self._entry: ConfigEntry = entry
        self._device: DeviceEntry = device
        self._event_callback: PipelineEventCallback = event_callback
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(QUEUE_MAX_CHUNKS)
        self._stream = QueueAsyncIterable(self._queue)

    async def run(self):
        """Run the managed pipeline."""

        _LOGGER.debug("Starting pipeline manager")

        while True:
            try:
                await assist_pipeline.async_pipeline_from_audio_stream(
                        hass=self._hass,
                        context=Context(),
                        event_callback=self._event_callback,
                        stt_stream=self._stream,
                        stt_metadata=stt.SpeechMetadata(
                          language = "",
                          format=stt.AudioFormats.WAV,
                          codec=stt.AudioCodecs.PCM,
                          bit_rate=stt.AudioBitRates.BITRATE_16,
                          sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                          channel=stt.AudioChannels.CHANNEL_MONO,
                        ),
                        start_stage=PipelineStage.WAKE_WORD,
                        device_id = self._device.id,
                        )

                _LOGGER.debug("Pipeline finished, starting over")
            except WakeWordDetectionError as e:
                if e.code == "wake-provider-missing":
                    _LOGGER.warning("Wakeword provider missing from pipeline.  Maybe not set up yet? Waiting and trying again.")
                    await asyncio.sleep(2)
                else:
                    raise



    def enqueue_chunk(self, chunk: bytes):
        """Enqueue an audio chunk, or clear the queue if it's full."""
        try:
            self._queue.put_nowait(chunk)
        except asyncio.QueueFull:
            _LOGGER.error("Chunk queue full, dumping contents")
            while True:
                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
