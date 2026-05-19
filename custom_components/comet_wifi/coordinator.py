"""Comet WiFi device coordinator."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Callable

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_TOPIC_PREFIX,
    CONF_ACCOUNT_ID,
    CONF_DEVICE_ID,
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    REG_POLL,
    PAYLOAD_POLL_ALL,
    PAYLOAD_POLL_TEMP,
)

_LOGGER = logging.getLogger(__name__)


class CometWifiDevice:
    """Represents a Comet WiFi thermostat device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the device."""
        self.hass = hass
        self.entry = entry
        self._prefix = entry.data[CONF_TOPIC_PREFIX]
        self._account_id = entry.data[CONF_ACCOUNT_ID]
        self._device_id = entry.data[CONF_DEVICE_ID]
        self._poll_interval = entry.data.get(
            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
        )

        self._data: dict[str, str] = {}
        self._listeners: list[Callable] = []
        self._unsubscribe_mqtt = None
        self._unsubscribe_timer = None

    @property
    def base_topic(self) -> str:
        """Return base topic for this device."""
        return f"{self._prefix}/{self._account_id}/{self._device_id}"

    @property
    def device_id(self) -> str:
        """Return device ID."""
        return self._device_id

    @property
    def account_id(self) -> str:
        """Return account ID."""
        return self._account_id

    def get_value(self, register: str) -> str | None:
        """Get the current value of a register."""
        return self._data.get(register)

    def add_listener(self, listener: Callable) -> None:
        """Add a state change listener."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable) -> None:
        """Remove a state change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def async_setup(self) -> None:
        """Set up MQTT subscriptions and polling."""
        topic = f"{self.base_topic}/V/#"

        @callback
        def message_received(msg):
            """Handle incoming MQTT messages."""
            register = msg.topic.split("/")[-1]
            self._data[register] = msg.payload
            _LOGGER.debug(
                "Received %s = %s for device %s",
                register,
                msg.payload,
                self._device_id,
            )
            for listener in self._listeners:
                listener()

        self._unsubscribe_mqtt = await mqtt.async_subscribe(
            self.hass, topic, message_received
        )

        self._unsubscribe_timer = async_track_time_interval(
            self.hass,
            self._async_poll,
            timedelta(minutes=self._poll_interval),
        )

        # Initial poll to get current values
        await self.async_poll_all()

    async def async_teardown(self) -> None:
        """Clean up subscriptions and timers."""
        if self._unsubscribe_mqtt:
            self._unsubscribe_mqtt()
        if self._unsubscribe_timer:
            self._unsubscribe_timer()

    async def async_poll_all(self) -> None:
        """Request all values from the device."""
        topic = f"{self.base_topic}/S/{REG_POLL}"
        await mqtt.async_publish(self.hass, topic, PAYLOAD_POLL_ALL)

    async def async_poll_temp(self) -> None:
        """Request current temperature from the device."""
        topic = f"{self.base_topic}/S/{REG_POLL}"
        await mqtt.async_publish(self.hass, topic, PAYLOAD_POLL_TEMP)

    async def async_set_register(self, register: str, payload: str) -> None:
        """Set a register value on the device."""
        topic = f"{self.base_topic}/S/{register}"
        await mqtt.async_publish(self.hass, topic, payload, retain=True)

    async def _async_poll(self, _now=None) -> None:
        """Periodic poll callback."""
        await self.async_poll_temp()

    @staticmethod
    def hex_to_temp(value: str) -> float | None:
        """Convert hex string like '#20' to temperature in °C."""
        try:
            return int(value[1:3], base=16) / 2
        except (ValueError, IndexError):
            return None

    @staticmethod
    def temp_to_hex(temp: float) -> str:
        """Convert temperature in °C to hex string like '#20'."""
        return f"#{int(temp * 2):02x}"
