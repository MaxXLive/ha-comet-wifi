# Comet WiFi Thermostat – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for **Eurotronic Comet WiFi** thermostats via MQTT.

## Features

- 🌡️ **Climate Entity** – Set and read target/current temperature
- 🔋 **Battery Sensor** – Monitor battery status
- ⚙️ **Options Sensor** – Raw A3 register value
- 🔒 **Keylock Switch** – Enable/disable child lock
- 🔄 **Display Rotation Switch** – Rotate display 180°
- ☀️ **Summer Mode Switch** – Activate summer mode
- 🔄 **Refresh Button** – Manually poll current values
- ⏱️ **Automatic Polling** – Configurable interval (default: 30 min)

## Prerequisites

1. **Mosquitto MQTT Broker** running on Home Assistant
2. **DNS redirection** of `mqtt.eurotronic.io` / `mqtt1.eurotronic.io` / `mqtt3.eurotronic.io` to your HA IP (e.g. via AdGuard Home, Pi-hole, or Dnsmasq)
3. **MQTT credentials** of the thermostat (sniffed via Wireshark/tcpdump)

## Installation

### HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add this repository URL, category: Integration
3. Search for "Comet WiFi" and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/comet_wifi/` to your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Comet WiFi Thermostat**
3. Enter:
   - **Name**: Friendly name (e.g. "Wohnzimmer")
   - **Topic Prefix**: Usually `02` or `03`
   - **Account ID**: From MQTT topic (e.g. `000154A4`)
   - **Device ID**: MAC address from MQTT topic (e.g. `D43D395938CE`)
   - **Poll Interval**: Minutes between automatic temperature polls (default: 30)

### Finding your device details

Connect to your MQTT broker with MQTT Explorer and look for topics like:
```
02/000154A4/D43D395938CE/V/A0
^^/^^^^^^^^/^^^^^^^^^^^^
|  |        |
|  |        └── Device ID (MAC)
|  └── Account ID
└── Topic Prefix
```

## MQTT Topic Reference

| Register | Direction | Description |
|----------|-----------|-------------|
| A0 | R/W | Target temperature (hex, value/2 = °C) |
| A1 | R | Current temperature |
| A2 | R/W | Temperature offset |
| A3 | R/W | Options bitfield (keylock, summer, rotation) |
| A5 | R/W | Window open detection settings |
| A7 | R/W | Holiday settings |
| A8–AE | R/W | Weekday program |
| AF | W | Poll command (request values) |
| BD | R | Battery/device status |
| XX | R/W | Connection verify |

## Credits

Based on research from [homeassistant.com.de](https://homeassistant.com.de/homeassistant/comet-wifi-thermostate-und-home-assistant/) and community contributions.

## License

MIT
