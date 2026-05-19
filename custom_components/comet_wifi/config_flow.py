"""Config flow for Comet WiFi Thermostat."""
from __future__ import annotations

import asyncio
import logging
import re

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_TOPIC_PREFIX,
    CONF_ACCOUNT_ID,
    CONF_DEVICE_ID,
    CONF_POLL_INTERVAL,
    DEFAULT_PREFIX,
    DEFAULT_POLL_INTERVAL,
    PAYLOAD_POLL_ALL,
    REG_POLL,
)

_LOGGER = logging.getLogger(__name__)

DISCOVERY_TIMEOUT = 30


class CometWifiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Comet WiFi."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, dict] = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step - choose auto or manual."""
        if user_input is not None:
            if user_input.get("setup_method") == "auto":
                return await self.async_step_discover()
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("setup_method", default="auto"): vol.In(
                        {
                            "auto": "Automatisch erkennen",
                            "manual": "Manuell eingeben",
                        }
                    ),
                }
            ),
        )

    async def async_step_discover(self, user_input=None):
        """Discover Comet WiFi devices on MQTT."""
        if user_input is not None:
            if user_input.get("device") == "_retry":
                # Re-run discovery
                return await self.async_step_discover()

            # User selected a device
            device_key = user_input["device"]
            device = self._discovered_devices[device_key]

            await self.async_set_unique_id(
                f"comet_wifi_{device['device_id']}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Comet WiFi {device['device_id'][-6:]}",
                data={
                    CONF_NAME: f"Comet WiFi {device['device_id'][-6:]}",
                    CONF_TOPIC_PREFIX: device["prefix"],
                    CONF_ACCOUNT_ID: device["account_id"],
                    CONF_DEVICE_ID: device["device_id"],
                    CONF_POLL_INTERVAL: DEFAULT_POLL_INTERVAL,
                },
            )

        # Scan for devices
        self._discovered_devices = {}
        unsubscribes = []

        @callback
        def message_received(msg):
            """Handle discovery messages."""
            topic = msg.topic
            # Skip system topics
            if topic.startswith("$"):
                return
            parts = topic.split("/")
            if len(parts) == 5:
                prefix, account_id, device_id, direction, register = parts
                # Accept both V (value) and S (set/retained) messages
                if direction in ("V", "S") and re.match(
                    r"^[0-9A-Fa-f]+$", account_id
                ):
                    key = f"{prefix}/{account_id}/{device_id}"
                    if key not in self._discovered_devices:
                        self._discovered_devices[key] = {
                            "prefix": prefix,
                            "account_id": account_id,
                            "device_id": device_id,
                        }
                        _LOGGER.debug("Discovered Comet WiFi: %s", key)

        try:
            # Subscribe to all topics to catch retained messages too
            unsub = await mqtt.async_subscribe(
                self.hass, "#", message_received
            )
            unsubscribes.append(unsub)

            # Trigger polls on any already-known devices from other entries
            for entry in self._async_current_entries():
                if entry.data.get(CONF_DEVICE_ID):
                    prefix = entry.data.get(CONF_TOPIC_PREFIX, DEFAULT_PREFIX)
                    acc = entry.data[CONF_ACCOUNT_ID]
                    dev = entry.data[CONF_DEVICE_ID]
                    poll_topic = f"{prefix}/{acc}/{dev}/S/{REG_POLL}"
                    await mqtt.async_publish(
                        self.hass, poll_topic, PAYLOAD_POLL_ALL
                    )

            await asyncio.sleep(DISCOVERY_TIMEOUT)
        finally:
            for unsub in unsubscribes:
                unsub()

        if not self._discovered_devices:
            return self.async_show_form(
                step_id="not_found",
                data_schema=vol.Schema({}),
                errors={"base": "no_devices_found"},
            )

        # Filter out already configured devices
        configured = set()
        for entry in self._async_current_entries():
            configured.add(entry.data.get(CONF_DEVICE_ID))

        available = {
            k: v
            for k, v in self._discovered_devices.items()
            if v["device_id"] not in configured
        }

        if not available:
            return self.async_abort(reason="all_devices_configured")

        self._discovered_devices = available

        device_options = {
            k: f"{v['device_id']} ({v['prefix']}/{v['account_id']})"
            for k, v in available.items()
        }

        return self.async_show_form(
            step_id="discover",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(device_options),
                }
            ),
        )

    async def async_step_not_found(self, user_input=None):
        """Handle case when no devices found - offer retry or manual."""
        if user_input is not None:
            next_step = user_input.get("next_step", "manual")
            if next_step == "retry":
                return await self.async_step_discover()
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="not_found",
            data_schema=vol.Schema(
                {
                    vol.Required("next_step", default="retry"): vol.In(
                        {
                            "retry": "Erneut suchen",
                            "manual": "Manuell eingeben",
                        }
                    ),
                }
            ),
        )

    async def async_step_manual(self, user_input=None):
        """Handle manual configuration."""
        errors = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].upper().replace(":", "")
            account_id = user_input[CONF_ACCOUNT_ID].upper()

            if not re.match(r"^[0-9A-F]+$", device_id):
                errors[CONF_DEVICE_ID] = "invalid_device_id"
            elif not re.match(r"^[0-9A-F]+$", account_id):
                errors[CONF_ACCOUNT_ID] = "invalid_account_id"
            else:
                user_input[CONF_DEVICE_ID] = device_id
                user_input[CONF_ACCOUNT_ID] = account_id

                await self.async_set_unique_id(f"comet_wifi_{device_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="Comet WiFi"): str,
                    vol.Required(
                        CONF_TOPIC_PREFIX, default=DEFAULT_PREFIX
                    ): str,
                    vol.Required(CONF_ACCOUNT_ID): str,
                    vol.Required(CONF_DEVICE_ID): str,
                    vol.Optional(
                        CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                }
            ),
            errors=errors,
        )
