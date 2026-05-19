"""Climate platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, REG_TARGET_TEMP, REG_CURRENT_TEMP


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Comet WiFi climate entity."""
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CometWifiClimate(device, entry)])


class CometWifiClimate(ClimateEntity):
    """Comet WiFi Climate entity."""

    _attr_has_entity_name = True
    _attr_name = "Thermostat"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.HEAT
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_icon = "mdi:temperature-celsius"

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the climate entity."""
        self._device = device
        self._attr_unique_id = f"comet_wifi_{device.device_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=entry.data.get("name", f"Comet WiFi {device.device_id}"),
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to device updates."""
        self._device.add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from device updates."""
        self._device.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        """Handle updated data from device."""
        self.async_write_ha_state()

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        value = self._device.get_value(REG_CURRENT_TEMP)
        if value is None:
            return None
        return self._device.hex_to_temp(value)

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        value = self._device.get_value(REG_TARGET_TEMP)
        if value is None:
            return None
        return self._device.hex_to_temp(value)

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        payload = self._device.temp_to_hex(temp)
        await self._device.async_set_register(REG_TARGET_TEMP, payload)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode (only heat is supported)."""
