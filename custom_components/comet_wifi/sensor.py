"""Sensor platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, REG_BATTERY, REG_OPTIONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Comet WiFi sensors."""
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CometWifiBatterySensor(device, entry),
            CometWifiOptionsSensor(device, entry),
        ]
    )


class CometWifiBatterySensor(SensorEntity):
    """Battery status sensor."""

    _attr_has_entity_name = True
    _attr_name = "Batterie"
    _attr_icon = "mdi:battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._device = device
        self._attr_unique_id = f"comet_wifi_{device.device_id}_battery"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to device updates."""
        self._device.add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from device updates."""
        self._device.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        """Handle updated data."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Return the raw battery register value."""
        return self._device.get_value(REG_BATTERY)


class CometWifiOptionsSensor(SensorEntity):
    """Options register sensor."""

    _attr_has_entity_name = True
    _attr_name = "Optionen"
    _attr_icon = "mdi:cog"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._device = device
        self._attr_unique_id = f"comet_wifi_{device.device_id}_options"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to device updates."""
        self._device.add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from device updates."""
        self._device.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        """Handle updated data."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Return the raw options register value."""
        return self._device.get_value(REG_OPTIONS)
