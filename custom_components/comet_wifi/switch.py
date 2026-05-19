"""Switch platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    REG_OPTIONS,
    PAYLOAD_KEYLOCK_ON,
    PAYLOAD_KEYLOCK_OFF,
    PAYLOAD_ROTATE_ON,
    PAYLOAD_ROTATE_OFF,
    PAYLOAD_SUMMER_ON,
    PAYLOAD_SUMMER_OFF,
)


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
                device,
                entry,
                key="keylock",
                name="Tastensperre",
                icon="mdi:lock",
                payload_on=PAYLOAD_KEYLOCK_ON,
                payload_off=PAYLOAD_KEYLOCK_OFF,
            ),
            CometWifiSwitch(
                device,
                entry,
                key="rotate",
                name="Display drehen",
                icon="mdi:screen-rotation",
                payload_on=PAYLOAD_ROTATE_ON,
                payload_off=PAYLOAD_ROTATE_OFF,
            ),
            CometWifiSwitch(
                device,
                entry,
                key="summer",
                name="Sommermodus",
                icon="mdi:white-balance-sunny",
                payload_on=PAYLOAD_SUMMER_ON,
                payload_off=PAYLOAD_SUMMER_OFF,
            ),
        ]
    )


class CometWifiSwitch(SwitchEntity):
    """Comet WiFi option switch."""

    _attr_has_entity_name = True
    _attr_assumed_state = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        device,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        payload_on: str,
        payload_off: str,
    ) -> None:
        """Initialize the switch."""
        self._device = device
        self._key = key
        self._payload_on = payload_on
        self._payload_off = payload_off
        self._is_on = False

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
        """Handle updated data - try to parse A3 for switch state."""
        value = self._device.get_value(REG_OPTIONS)
        if value and len(value) >= 5:
            try:
                # Parse A3 register as bitfield
                raw = int(value[1:], 16)
                # Bit mapping (derived from known payloads):
                # Bit 2 (0x04): keylock
                # Bit 8 (0x100): rotate display
                # Bit 7 (0x80): summer mode
                if self._key == "keylock":
                    self._is_on = bool(raw & 0x04)
                elif self._key == "rotate":
                    self._is_on = bool(raw & 0x100)
                elif self._key == "summer":
                    self._is_on = bool(raw & 0x80)
            except (ValueError, IndexError):
                pass
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._device.async_set_register(REG_OPTIONS, self._payload_on)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._device.async_set_register(REG_OPTIONS, self._payload_off)
        self._is_on = False
        self.async_write_ha_state()
