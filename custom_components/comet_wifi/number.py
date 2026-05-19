"""Number platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, REG_TEMP_OFFSET, REG_WINDOW_OPEN, REG_COMFORT_TEMP


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Comet WiFi number entities."""
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CometWifiTempOffsetNumber(device, entry),
            CometWifiComfortTempNumber(device, entry),
            CometWifiWodSensitivityNumber(device, entry),
            CometWifiWodDurationNumber(device, entry),
        ]
    )


class CometWifiBaseNumber(NumberEntity):
    """Base class for Comet WiFi number entities."""

    _attr_has_entity_name = True

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self._device = device
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


class CometWifiTempOffsetNumber(CometWifiBaseNumber):
    """Temperature offset setting (-3.0 to +3.0°C)."""

    _attr_name = "Temperatur-Offset"
    _attr_icon = "mdi:thermometer-plus"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = -3.0
    _attr_native_max_value = 3.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_offset_number"

    @property
    def native_value(self) -> float | None:
        """Return current offset from A2 register."""
        value = self._device.get_value(REG_TEMP_OFFSET)
        if not value or len(value) < 3:
            return None
        try:
            raw = int(value[1:3], 16)
            if raw > 127:
                raw -= 256
            return raw / 2
        except (ValueError, IndexError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set temperature offset via A2 register."""
        # Convert °C to signed byte: value * 2, then to unsigned hex
        raw = int(value * 2)
        if raw < 0:
            raw += 256
        payload = f"#{raw:02X}"
        await self._device.async_set_register(REG_TEMP_OFFSET, payload)


class CometWifiComfortTempNumber(CometWifiBaseNumber):
    """Comfort temperature setting (4.0 to 28.0°C)."""

    _attr_name = "Komfort-Temperatur"
    _attr_icon = "mdi:thermometer-high"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 4.0
    _attr_native_max_value = 28.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.SLIDER

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_comfort_temp_number"

    @property
    def native_value(self) -> float | None:
        """Return comfort temperature from A6 register."""
        value = self._device.get_value(REG_COMFORT_TEMP)
        if not value or len(value) < 3:
            return None
        try:
            raw = int(value[1:3], 16)
            return raw / 2
        except (ValueError, IndexError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set comfort temperature via A6 register."""
        payload = f"#{int(value * 2):02X}"
        await self._device.async_set_register(REG_COMFORT_TEMP, payload)


class CometWifiWodSensitivityNumber(CometWifiBaseNumber):
    """Window-open detection sensitivity (temperature drop in °C)."""

    _attr_name = "Fenster-Offen Empfindlichkeit"
    _attr_icon = "mdi:window-open-variant"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 1
    _attr_native_max_value = 5
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_wod_sensitivity"

    @property
    def native_value(self) -> int | None:
        """Return sensitivity (first byte of A5)."""
        value = self._device.get_value(REG_WINDOW_OPEN)
        if not value or len(value) < 5:
            return None
        try:
            return int(value[1:3], 16)
        except (ValueError, IndexError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set window-open sensitivity, preserving duration."""
        current = self._device.get_value(REG_WINDOW_OPEN)
        duration = 10  # default 10 minutes
        if current and len(current) >= 5:
            try:
                duration = int(current[3:5], 16)
            except ValueError:
                pass
        payload = f"#{int(value):02X}{duration:02X}"
        await self._device.async_set_register(REG_WINDOW_OPEN, payload)


class CometWifiWodDurationNumber(CometWifiBaseNumber):
    """Window-open detection duration (minutes)."""

    _attr_name = "Fenster-Offen Dauer"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "min"
    _attr_native_min_value = 5
    _attr_native_max_value = 30
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_wod_duration"

    @property
    def native_value(self) -> int | None:
        """Return duration (second byte of A5)."""
        value = self._device.get_value(REG_WINDOW_OPEN)
        if not value or len(value) < 5:
            return None
        try:
            return int(value[3:5], 16)
        except (ValueError, IndexError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set window-open duration, preserving sensitivity."""
        current = self._device.get_value(REG_WINDOW_OPEN)
        sensitivity = 4  # default 4°C
        if current and len(current) >= 5:
            try:
                sensitivity = int(current[1:3], 16)
            except ValueError:
                pass
        payload = f"#{sensitivity:02X}{int(value):02X}"
        await self._device.async_set_register(REG_WINDOW_OPEN, payload)
