"""Sensor platform for hassmic integration."""

from __future__ import annotations

import enum
import logging
import re

from homeassistant.components.assist_pipeline.pipeline import (
    PipelineEvent,
    PipelineEventType,
)
from homeassistant.components.sensor import ENTITY_ID_FORMAT, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import init_entity
from .const import STATE_DETECTED, STATE_ERROR, STATE_LISTENING

_LOGGER = logging.getLogger(__name__)

# A list of the sensors provided by each instance of this integration
class WhichSensor(enum.StrEnum):
    """The list of possible sensors types."""

    # State of wakeword detection
    WAKE = "wake"

    # Speech to text of current pipeline run
    STT = "stt"

    # Intent of curent run
    INTENT = "intent"

    # Text-to-speech of current run
    TTS = "tts"

    # Overall current pipeline state
    STATE = "state"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize hassmic config entry for sensors."""

    async_add_entities([hassmicSensorEntity(hass, config_entry, key) for key in WhichSensor])


class hassmicSensorEntity(SensorEntity):
    """hassmic Sensor."""

    _attr_native_value = STATE_IDLE
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, key: WhichSensor) -> None:
        """Initialize hassmic Sensor."""
        super().__init__()
        init_entity(self, key.value, config_entry)
        self._key: WhichSensor = key

        id_candidate = re.sub(
                r"[^A-Za-z0-9_]", "_", f"{config_entry.title}_{key.value}".lower())
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, id_candidate, hass=hass)

    def handle_connection_state_change(self, new_state: bool):
      """Handle a connection state change."""
      self.available = new_state
      self.schedule_update_ha_state()

    def handle_pipeline_event(self, event: PipelineEvent): # noqa: C901
        """Handle a `PipelineEvent` and perform any required state updates.

        This is called on *every* sensor for *every* pipeline event.
        """

        # if we're not connected (sensor is unavailable), ignore pipeline state
        # updates
        if not self.available:
          return

        # For the state sensor, just set the state to the event type and don't
        # do any processing.
        if self._key == WhichSensor.STATE:
            self._attr_native_value = event.type
            self.attr_extra_state_attributes = event.data
            self.schedule_update_ha_state()
            return


        match event.type:
            # TODO - figure out what the best thing to do with run_start and
            # run_end is.
            #
            ## If we're starting or ending a pipeline, reset all the sensors.
            #case PipelineEventType.RUN_START | PipelineEventType.RUN_END:
            #    self._attr_native_value = STATE_IDLE

            # If we encountered an error, set all sensors to error
            case PipelineEventType.ERROR:
                if event.data.get("code", None) != "wake-word-timeout":
                    self._attr_native_value = STATE_ERROR

            # Wakeword start and end set the WAKE sensor
            case PipelineEventType.WAKE_WORD_START:
                if self._key == WhichSensor.WAKE:
                    self._attr_native_value = STATE_LISTENING
                    self._attr_extra_state_attributes = {
                            "entity_id": event.data.get("entity_id", None)
                            }

            case PipelineEventType.WAKE_WORD_END:
                if self._key == WhichSensor.WAKE:
                    self._attr_native_value = STATE_DETECTED

            # We don't care about these for now, but enumerate them explicitly
            # in case we do later.
            case PipelineEventType.STT_START | PipelineEventType.STT_VAD_START | PipelineEventType.STT_VAD_END:
                pass

            # When STT ends, the event data has the interpreted STT text
            case PipelineEventType.STT_END:
                if self._key == WhichSensor.STT:
                    stt_out = event.data.get("stt_output", None)
                    if stt_out:
                        txt = stt_out.get("text", None)
                        self._attr_native_value = txt

            # Do nothing for INTENT_START
            case PipelineEventType.INTENT_START:
                pass

            # INTENT_END has the conversation response
            case PipelineEventType.INTENT_END:
                if self._key == WhichSensor.INTENT:
                    iout = event.data.get("intent_output", None)
                    if iout is None:
                        _LOGGER.warning("Got no intent_output data from INTENT_END event")
                        return
                    response = iout.get("response", None)
                    conversation_id = iout.get("conversation_id", None)
                    resp = {}
                    if response:
                        resp["response_type"] = response.get("response_type", None)
                        resp["response_data"] = response.get("data", None)
                        resp["speech"] = response.get("speech", None)

                    # speech type can be one of "plain" (default) or "ssml"
                    speech = ""
                    speech_type = None
                    if s := resp.get("speech"):
                        if ps := s.get("plain", None):
                            speech = ps.get("speech", None)
                            speech_type = "plain"
                        elif ssml := s.get("ssml", None):
                            speech = ssml.get("speech", None)
                            speech_type = "ssml"

                    if not speech or not speech_type:
                        _LOGGER.warning("No speech found in intent output")

                    self._attr_native_value = speech
                    self._attr_extra_state_attributes = {
                            **resp,
                            "speech_type": speech_type,
                            "conversation_id": conversation_id,
                    }

            # Do nothing for TTS_START
            case PipelineEventType.TTS_START:
                pass

            # TTS_END has the media URL
            case PipelineEventType.TTS_END:
                if self._key == WhichSensor.TTS:
                    if o := event.data.get("tts_output"):
                        self._attr_native_value = o.get("media_id", None)
                        self._attr_extra_state_attributes = o
                    else:
                        _LOGGER.warning("No tts_output found in TTS_END event")



        self.schedule_update_ha_state()

