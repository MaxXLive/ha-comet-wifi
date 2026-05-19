"""Sensor platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL


# Register constants
REG_BATTERY = "BD"
REG_OPTIONS = "A3"
REG_RSSI = "B3"
REG_FIRMWARE = "B2"
REG_DEVICE_NAME = "B1"
REG_NETWORK = "B6"
REG_TEMP_OFFSET = "A2"
REG_WINDOW_OPEN = "A5"
REG_VALVE = "BE"
REG_COMFORT_TEMP = "A6"
REG_BSSID = "BA"
REG_SCHEDULE_STATE = "A4"


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
            CometWifiRssiSensor(device, entry),
            CometWifiFirmwareSensor(device, entry),
            CometWifiIPSensor(device, entry),
            CometWifiOptionsSensor(device, entry),
            CometWifiTempOffsetSensor(device, entry),
            CometWifiWindowOpenSensor(device, entry),
            CometWifiValveSensor(device, entry),
            CometWifiComfortTempSensor(device, entry),
            CometWifiBssidSensor(device, entry),
            CometWifiScheduleStateSensor(device, entry),
        ]
    )


class CometWifiBaseSensor(SensorEntity):
    """Base class for Comet WiFi sensors."""

    _attr_has_entity_name = True

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._device = device
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
        """Handle updated data."""
        self.async_write_ha_state()


class CometWifiBatterySensor(CometWifiBaseSensor):
    """Battery level sensor."""

    _attr_name = "Batterie"
    _attr_icon = "mdi:battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_battery"

    @property
    def native_value(self) -> int | None:
        """Return battery percentage from BD register."""
        value = self._device.get_value(REG_BATTERY)
        if not value or len(value) < 3:
            return None
        try:
            # BD format: first byte is battery level on scale 0-8 (8=full)
            level = int(value[1:3], 16)
            percentage = round(level / 8 * 100)
            return min(100, max(0, percentage))
        except (ValueError, IndexError):
            return None


class CometWifiRssiSensor(CometWifiBaseSensor):
    """WiFi signal strength sensor."""

    _attr_name = "WiFi Signal"
    _attr_icon = "mdi:wifi"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_rssi"

    @property
    def native_value(self) -> int | None:
        """Return RSSI from B3 register."""
        value = self._device.get_value(REG_RSSI)
        if not value:
            return None
        try:
            # B3 format: #-58 (includes sign)
            return int(value[1:])
        except (ValueError, IndexError):
            return None


class CometWifiFirmwareSensor(CometWifiBaseSensor):
    """Firmware version sensor."""

    _attr_name = "Firmware"
    _attr_icon = "mdi:information-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_firmware"

    @property
    def native_value(self) -> str | None:
        """Return firmware version from B2 register (ASCII encoded)."""
        value = self._device.get_value(REG_FIRMWARE)
        if not value or len(value) < 3:
            return None
        try:
            return bytes.fromhex(value[1:]).decode("ascii")
        except (ValueError, UnicodeDecodeError):
            return value


class CometWifiIPSensor(CometWifiBaseSensor):
    """IP address sensor."""

    _attr_name = "IP-Adresse"
    _attr_icon = "mdi:ip-network"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_ip"

    @property
    def native_value(self) -> str | None:
        """Return IP address from B6 register."""
        value = self._device.get_value(REG_NETWORK)
        if not value or len(value) < 11:
            return None
        try:
            # B6 format: #00XXYYZZ... where XX.YY.ZZ.WW is IP at bytes 1-4
            hex_str = value[3:11]  # Skip # and first byte (00)
            octets = [int(hex_str[i : i + 2], 16) for i in range(0, 8, 2)]
            return f"{octets[0]}.{octets[1]}.{octets[2]}.{octets[3]}"
        except (ValueError, IndexError):
            return value


class CometWifiOptionsSensor(CometWifiBaseSensor):
    """Options register sensor showing decoded flags."""

    _attr_name = "Optionen"
    _attr_icon = "mdi:cog"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_options"

    @property
    def native_value(self) -> str | None:
        """Return decoded flags from A3 register."""
        value = self._device.get_value(REG_OPTIONS)
        if not value or len(value) < 3:
            return None
        try:
            byte0 = int(value[1:3], 16)
            flags = byte0 & 0x07
            parts = []
            if flags & 0x04:
                parts.append("Tastensperre")
            if flags & 0x02:
                parts.append("Display gedreht")
            if flags & 0x01:
                parts.append("Sommermodus")
            return ", ".join(parts) if parts else "Keine"
        except (ValueError, IndexError):
            return value


class CometWifiTempOffsetSensor(CometWifiBaseSensor):
    """Temperature offset sensor."""

    _attr_name = "Temperatur-Offset"
    _attr_icon = "mdi:thermometer-plus"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_temp_offset"

    @property
    def native_value(self) -> float | None:
        """Return temperature offset from A2 register."""
        value = self._device.get_value(REG_TEMP_OFFSET)
        if not value or len(value) < 3:
            return None
        try:
            raw = int(value[1:3], 16)
            # Signed byte: offset in 0.5°C steps
            if raw > 127:
                raw -= 256
            return raw / 2
        except (ValueError, IndexError):
            return None


class CometWifiWindowOpenSensor(CometWifiBaseSensor):
    """Window open detection settings sensor."""

    _attr_name = "Fenster-Offen Einstellung"
    _attr_icon = "mdi:window-open-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_window_open"

    @property
    def native_value(self) -> str | None:
        """Return window-open settings from A5 (temp drop °C, duration min)."""
        value = self._device.get_value(REG_WINDOW_OPEN)
        if not value or len(value) < 5:
            return None
        try:
            # A5 format: #XXYY → XX=temp drop in °C, YY=duration in minutes
            temp_drop = int(value[1:3], 16)
            duration = int(value[3:5], 16)
            return f"-{temp_drop}°C / {duration} Min"
        except (ValueError, IndexError):
            return value


class CometWifiValveSensor(CometWifiBaseSensor):
    """Valve/motor position sensor."""

    _attr_name = "Ventilposition"
    _attr_icon = "mdi:valve"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_valve"

    @property
    def native_value(self) -> int | None:
        """Return valve position from BE register (byte1 = 0-100%)."""
        value = self._device.get_value(REG_VALVE)
        if not value or len(value) < 5:
            return None
        try:
            # BE format: #XXYYZZ → byte1 (YY) = valve position percentage
            position = int(value[3:5], 16)
            return min(100, max(0, position))
        except (ValueError, IndexError):
            return None


class CometWifiComfortTempSensor(CometWifiBaseSensor):
    """Comfort temperature sensor."""

    _attr_name = "Komfort-Temperatur"
    _attr_icon = "mdi:thermometer-high"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_comfort_temp"

    @property
    def native_value(self) -> float | None:
        """Return comfort temperature from A6 register (same encoding as A0)."""
        value = self._device.get_value(REG_COMFORT_TEMP)
        if not value or len(value) < 3:
            return None
        try:
            raw = int(value[1:3], 16)
            return raw / 2
        except (ValueError, IndexError):
            return None


class CometWifiBssidSensor(CometWifiBaseSensor):
    """Router BSSID/MAC sensor."""

    _attr_name = "Router-MAC"
    _attr_icon = "mdi:router-wireless"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_bssid"

    @property
    def native_value(self) -> str | None:
        """Return router BSSID from BA register."""
        value = self._device.get_value(REG_BSSID)
        if not value or len(value) < 3:
            return None
        # BA format: #XX:XX:XX:XX:XX:XX (MAC address as text)
        return value[1:]


class CometWifiScheduleStateSensor(CometWifiBaseSensor):
    """Schedule/heating profile state sensor."""

    _attr_name = "Heizprofil-Status"
    _attr_icon = "mdi:calendar-clock"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(device, entry)
        self._attr_unique_id = f"comet_wifi_{device.device_id}_schedule_state"

    @property
    def native_value(self) -> str | None:
        """Return schedule state from A4 register."""
        value = self._device.get_value(REG_SCHEDULE_STATE)
        if not value or len(value) < 3:
            return None
        try:
            # A4 format: #XXYYZZZZ... byte0 = mode
            mode_byte = int(value[1:3], 16)
            modes = {0: "Aus", 1: "Manuell", 2: "Automatik"}
            return modes.get(mode_byte, f"Modus {mode_byte}")
        except (ValueError, IndexError):
            return value
