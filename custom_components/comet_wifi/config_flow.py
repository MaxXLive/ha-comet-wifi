"""Config flow for Comet WiFi Thermostat."""
from __future__ import annotations

import re

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_TOPIC_PREFIX,
    CONF_ACCOUNT_ID,
    CONF_DEVICE_ID,
    CONF_POLL_INTERVAL,
    DEFAULT_PREFIX,
    DEFAULT_POLL_INTERVAL,
)


class CometWifiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Comet WiFi."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
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
            step_id="user",
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
