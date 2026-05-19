"""Button platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Comet WiFi buttons."""
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CometWifiRefreshButton(device, entry)])


class CometWifiRefreshButton(ButtonEntity):
    """Button to manually poll current values."""

    _attr_has_entity_name = True
    _attr_name = "Temperatur abrufen"
    _attr_icon = "mdi:refresh"

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._device = device
        self._attr_unique_id = f"comet_wifi_{device.device_id}_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._device.async_poll_all()
