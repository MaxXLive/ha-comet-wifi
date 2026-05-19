"""Comet WiFi Thermostat integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import CometWifiDevice


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Comet WiFi from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    device = CometWifiDevice(hass, entry)
    await device.async_setup()

    hass.data[DOMAIN][entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        device = hass.data[DOMAIN].pop(entry.entry_id)
        await device.async_teardown()

    return unload_ok
