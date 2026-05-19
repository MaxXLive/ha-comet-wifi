"""Switch platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, REG_OPTIONS

# A3 flags bitfield (byte0 & 0x07):
FLAG_SUMMER = 0x01   # bit 0
FLAG_ROTATE = 0x02   # bit 1
FLAG_KEYLOCK = 0x04  # bit 2


def build_a3_payload(flags: int) -> str:
    """Build A3 SET payload from flags bitfield.

    Formula: byte0 = 0x20 | flags, byte1 = (~flags) & 0x07, byte2 = 0x00
    """
    byte0 = 0x20 | (flags & 0x07)
    byte1 = (~flags) & 0x07
    return f"#{byte0:02X}{byte1:02X}00"


def parse_a3_flags(value: str) -> int | None:
    """Parse current flags from A3 READ value. Returns flags bitfield."""
    if not value or len(value) < 3:
        return None
    try:
        byte0 = int(value[1:3], 16)
        return byte0 & 0x07
    except (ValueError, IndexError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Comet WiFi switches."""
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CometWifiSwitch(
                device, entry,
                key="summer",
                name="Sommermodus",
                icon="mdi:white-balance-sunny",
                flag_bit=FLAG_SUMMER,
            ),
            CometWifiSwitch(
                device, entry,
                key="rotate",
                name="Display drehen",
                icon="mdi:screen-rotation",
                flag_bit=FLAG_ROTATE,
            ),
            CometWifiSwitch(
                device, entry,
                key="keylock",
                name="Tastensperre",
                icon="mdi:lock",
                flag_bit=FLAG_KEYLOCK,
            ),
        ]
    )


class CometWifiSwitch(SwitchEntity):
    """Comet WiFi option switch with read-modify-write on A3 register."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        device,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        flag_bit: int,
    ) -> None:
        """Initialize the switch."""
        self._device = device
        self._key = key
        self._flag_bit = flag_bit

        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"comet_wifi_{device.device_id}_{key}"
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
        """Handle updated data from device."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on, based on actual A3 register."""
        flags = parse_a3_flags(self._device.get_value(REG_OPTIONS))
        if flags is None:
            return None
        return bool(flags & self._flag_bit)

    @property
    def available(self) -> bool:
        """Return True if A3 has been read at least once."""
        return self._device.get_value(REG_OPTIONS) is not None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on using read-modify-write."""
        current_flags = parse_a3_flags(self._device.get_value(REG_OPTIONS))
        if current_flags is None:
            current_flags = 0
        new_flags = current_flags | self._flag_bit
        payload = build_a3_payload(new_flags)
        await self._device.async_set_register(REG_OPTIONS, payload)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off using read-modify-write."""
        current_flags = parse_a3_flags(self._device.get_value(REG_OPTIONS))
        if current_flags is None:
            current_flags = 0
        new_flags = current_flags & ~self._flag_bit
        payload = build_a3_payload(new_flags)
        await self._device.async_set_register(REG_OPTIONS, payload)
