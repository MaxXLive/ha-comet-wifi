"""Switch platform for Comet WiFi Thermostat."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
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
    """Comet WiFi option switch (optimistic)."""

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
        self._payload_on = payload_on
        self._payload_off = payload_off
        self._is_on = False

        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"comet_wifi_{device.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
        )

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
