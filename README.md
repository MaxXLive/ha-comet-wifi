# Comet WiFi Thermostat – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for **Eurotronic Comet WiFi** thermostats via MQTT.

## Features

### Climate Control
- 🌡️ **Climate Entity** – Set and read target/current temperature (4–28°C, 0.5° steps)
- 🎯 **Comfort Temperature** – Configurable comfort temperature setting
- 📐 **Temperature Offset** – Calibration offset (-3.0 to +3.0°C)

### Switches (with real state feedback)
- 🔒 **Keylock** – Enable/disable child lock
- 🔄 **Display Rotation** – Rotate display 180°
- ☀️ **Summer Mode** – Valve fully closed, frost protection only

### Sensors (11 total)
- 🔋 **Battery** – Level in % (scale 0–8)
- 📶 **WiFi Signal** – RSSI in dBm
- 🌡️ **Comfort Temperature** – Current comfort temp setting
- 🔧 **Valve Position** – Motor/valve state (0–100%)
- 📋 **Options** – Decoded flags (human-readable)
- 📐 **Temperature Offset** – Current offset value
- 🪟 **Window-Open Settings** – Sensitivity + duration
- 📅 **Heating Profile Status** – Schedule mode (Off/Manual/Auto)
- 🏷️ **Firmware** – Device firmware version
- 🌐 **IP Address** – Device network address
- 📡 **Router MAC** – Connected BSSID

### Configuration (Number Entities)
- 📐 **Temperature Offset** – Slider -3.0 to +3.0°C (step 0.5)
- 🎯 **Comfort Temperature** – Slider 4.0 to 28.0°C (step 0.5)
- 🪟 **Window-Open Sensitivity** – Temperature drop threshold (1–5°C)
- ⏱️ **Window-Open Duration** – Detection window (5–30 min)

### Other
- 🔄 **Refresh Button** – Manually poll all device values
- 📡 **Auto-Discovery** – Find thermostats on your MQTT broker
- ⏱️ **Automatic Polling** – Configurable interval (default: 30 min)

## Prerequisites

1. **Mosquitto MQTT Broker** running on Home Assistant
2. **DNS redirection** of `mqtt.eurotronic.io` / `mqtt1.eurotronic.io` / `mqtt3.eurotronic.io` to your HA IP (e.g. via AdGuard Home, Pi-hole, or Dnsmasq)
3. **MQTT credentials** of the thermostat (sniffed via Wireshark/tcpdump during initial connection, or from the Eurotronic cloud API)

## Installation

### HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/MaxXLive/ha-comet-wifi`, category: Integration
3. Search for "Comet WiFi" and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/comet_wifi/` to your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Auto-Discovery (recommended)

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Comet WiFi Thermostat**
3. Select "Automatisch suchen" (auto-discover)
4. Wait ~30 seconds for the integration to find your thermostats
5. Select the found device and give it a name

### Manual Configuration

If auto-discovery doesn't find your device:

1. Select "Manuell eingeben" (manual entry)
2. Enter:
   - **Name**: Friendly name (e.g. "Wohnzimmer")
   - **Topic Prefix**: Usually `02`
   - **Account ID**: From MQTT topic (e.g. `000154A4`)
   - **Device ID**: MAC address without colons (e.g. `D43D395938CE`)
   - **Poll Interval**: Minutes between automatic polls (default: 30)

See the [Network Setup Guide](#network-setup-guide) below for how to find these values.

## How it Works

The Comet WiFi thermostat connects to Eurotronic's MQTT cloud broker. By redirecting the DNS of `mqtt.eurotronic.io` to your local Home Assistant, the thermostat connects to your Mosquitto broker instead.

The thermostat is battery-powered and does NOT publish values proactively. This integration **polls** the device periodically by sending a command to register `AF`, which triggers the thermostat to respond with all register values.

## MQTT Protocol Reference

### Topic Structure
```
{prefix}/{account_id}/{device_id}/S/{register}  → SET (write to device)
{prefix}/{account_id}/{device_id}/V/{register}  → VALUE (read from device)
```

### Complete Register Map

| Register | R/W | Format | Description |
|----------|-----|--------|-------------|
| **A0** | R/W | `#XX` (hex/2 = °C) | Target temperature |
| **A1** | R | `#XX` (hex/2 = °C) | Current (measured) temperature |
| **A2** | R/W | `#XX` (signed byte/2 = °C) | Temperature calibration offset |
| **A3** | R/W | `#XXYY` (bitfield) | Options flags (see below) |
| **A4** | R | `#XXYYZZZZ` | Heating profile/schedule state |
| **A5** | R/W | `#XXYY` (°C, minutes) | Window-open detection config |
| **A6** | R/W | `#XX` (hex/2 = °C) | Comfort temperature |
| **A7** | R/W | 8 bytes | Holiday profile (FFFFFFFFFFFFFFFF = off) |
| **A8–AE** | R/W | variable | Weekly schedule (Mon–Sun, `#` = empty) |
| **AF** | R/W | `#FFFFFFFF` | Poll command / response status |
| **B0** | R | text | Device identifier |
| **B1** | R | ASCII hex | Device name (e.g. "Comet Wifi Ver. 6.1") |
| **B2** | R | ASCII hex | Firmware version (e.g. "2.7.1.0") |
| **B3** | R | `#-XX` | WiFi RSSI in dBm |
| **B4** | R | `#00000000` | Unknown (error counter?) |
| **B5** | R | `#FF` | Unknown |
| **B6** | R | 10 bytes | Network info (byte0=type, bytes1-4=IP) |
| **B7** | R | `#00` | Unknown |
| **BA** | R | MAC format | Router BSSID |
| **BB** | R | `#00` | Unknown |
| **BC** | R | `#FF` | Unknown |
| **BD** | R | `#XXYY` | Battery (byte0=level 0-8, 8=full) |
| **BE** | R | `#XXYYZZ` | Valve/motor state (byte1=position %) |
| **BF** | R | ASCII hex | WiFi security string |

### A3 Options Register (Decoded)

The A3 register uses a bitfield in byte0:
- **Bit 0** (0x01): Summer mode
- **Bit 1** (0x02): Display rotation
- **Bit 2** (0x04): Keylock

**Reading:** `byte0 & 0x07` gives the flags state.

**Writing (SET):** Uses a 3-byte formula:
```
flags = desired state (combination of bits 0-2)
byte0 = 0x20 | flags
byte1 = (~flags) & 0x07
byte2 = 0x00
payload = f"#{byte0:02X}{byte1:02X}00"
```

Example: Turn on keylock + keep rotate on:
- flags = 0x06 (keylock=0x04 + rotate=0x02)
- payload = `#260100`

### Polling

The thermostat only responds when polled. Send to `S/AF`:
- `#FFFFFFFF` – Request ALL register values
- `#02000000` – Request temperature only (A0, A1)

## Network Setup Guide

The Comet WiFi thermostat normally connects to Eurotronic's cloud MQTT broker. To use it locally with Home Assistant, you redirect it to your own broker.

### Step 1: Install Mosquitto Broker

Install the **Mosquitto broker** addon in Home Assistant (Settings → Add-ons → Mosquitto broker).

### Step 2: DNS Redirection

Redirect the Eurotronic MQTT domains to your Home Assistant IP. The thermostat tries these brokers:
- `mqtt.eurotronic.io`
- `mqtt1.eurotronic.io`
- `mqtt3.eurotronic.io`

**Option A: AdGuard Home (recommended if already using)**
1. Go to AdGuard Home → Filters → DNS Rewrites
2. Add entries:
   - `mqtt.eurotronic.io` → `192.168.2.10` (your HA IP)
   - `mqtt1.eurotronic.io` → `192.168.2.10`
   - `mqtt3.eurotronic.io` → `192.168.2.10`

**Option B: Pi-hole**
1. Local DNS → DNS Records
2. Add the same three domains pointing to your HA IP

**Option C: Router DNS**
- Some routers allow static DNS entries or DNS rebinding exceptions

### Step 3: Sniff MQTT Credentials

The thermostat authenticates with a username (= Account ID) and password. To capture these:

1. **Temporarily** set Mosquitto to log all connection attempts:
   - In the Mosquitto addon config, enable verbose logging
   - Or watch the addon log while the thermostat connects
2. **Restart the thermostat** (remove + reinsert batteries)
3. Check the Mosquitto log for the login attempt — you'll see:
   ```
   New connection from 192.168.x.x on port 1883
   Username: 000154A4
   ```
4. The password can be captured with `tcpdump` / Wireshark on port 1883 (MQTT CONNECT packet, unencrypted), or by setting Mosquitto to `allow_anonymous true` temporarily and reading the AUTH fields

**Credentials format:**
- Username: 8-character hex string (e.g. `000154A4`) — this is also the Account ID
- Password: 16-character hex string (e.g. `9D9CB2C82E445114`)

### Step 4: Configure Mosquitto

Add the thermostat's credentials as a Mosquitto user:

1. In Home Assistant: Settings → Add-ons → Mosquitto → Configuration
2. Add under "Logins":
   ```yaml
   - username: "000154A4"
     password: "9D9CB2C82E445114"
   ```
3. Restart Mosquitto

### Step 5: Verify Connection

1. Restart the thermostat (remove/reinsert batteries)
2. Check Mosquitto logs — you should see a successful connection
3. Use **MQTT Explorer** (connect to your HA broker) to see topics appearing:
   ```
   02/000154A4/D43D395938CE/V/A1   →  #29
   ```

### Step 6: Install this Integration

Now install the integration (see Installation above) and either use auto-discovery or enter manually:

```
Topic Prefix:  02              (first part of the topic)
Account ID:    000154A4        (= MQTT username)
Device ID:     D43D395938CE    (= thermostat MAC without colons)
```

### Finding Device Details from MQTT Topics

If the thermostat is already connected, look at MQTT Explorer for topics like:
```
02/000154A4/D43D395938CE/V/A0
│  │        │
│  │        └── Device ID (MAC without colons, 12 hex chars)
│  └── Account ID (8 hex chars, = MQTT username)
└── Topic Prefix (usually "02")
```

### Troubleshooting

- **Thermostat doesn't connect:** Verify DNS is resolving correctly (`nslookup mqtt.eurotronic.io` from a device on the same network should return your HA IP)
- **Auth failure in Mosquitto logs:** Double-check username/password spelling, restart Mosquitto after adding credentials
- **No MQTT messages appear:** The thermostat must be polled first — install the integration, it will poll automatically
- **"Unauthorized login for 's'":** The thermostat tried a test connection with username 's' — this is normal during initial setup, ignore it

## Credits

Based on initial research from [homeassistant.com.de](https://homeassistant.com.de/homeassistant/comet-wifi-thermostate-und-home-assistant/) with extensive additional reverse engineering of the Eurotronic "Smart Living 2.0" Android app.

## License

MIT
