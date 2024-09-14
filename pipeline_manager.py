"""Defines a class to manage the assist pipeline."""

import asyncio
import aiofiles
import logging

from homeassistant.components import assist_pipeline, stt
from homeassistant.components.assist_pipeline.pipeline import PipelineStage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant

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

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Construct a new manager."""
        self._hass: HomeAssistant = hass
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(QUEUE_MAX_CHUNKS)
        self._stream = QueueAsyncIterable(self._queue)

    async def run(self):
        """Run the managed pipeline."""
        #self._pipeline = await assist_pipeline.get(self._hass)
        #_LOGGER.debug("Got pipeline: %s", repr(self._pipeline))
        _LOGGER.debug("Starting pipelinemanager")

        def cb(e):
            _LOGGER.debug("Got event from pipeline: %s", repr(e))

        #async with aiofiles.open('/tmp/assist.pcm', 'w') as f:
        #  while True:
        #    s = await self._queue.get()
        #    await f.write(s)
        #    _LOGGER.debug("wrote sample of size %d", len(s))
          
        while True:
            await assist_pipeline.async_pipeline_from_audio_stream(
                    hass=self._hass,
                    context=Context(),
                    event_callback=cb,
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
										)

            _LOGGER.debug("Pipeline finished, starting over")



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
