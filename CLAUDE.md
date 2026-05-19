# CLAUDE.md - Project Guidelines

## Project: ha-comet-wifi
Home Assistant HACS integration for Eurotronic Comet WiFi thermostats via local MQTT.

## Versioning
- Uses **Semantic Versioning** (MAJOR.MINOR.PATCH)
- Version is defined in `custom_components/comet_wifi/manifest.json` → `"version"`
- **Every commit message MUST include the version number** in format: `vX.Y.Z: description`
  - Example: `v1.0.0: initial release`
  - Example: `v1.1.0: add auto-discovery for devices`
  - Example: `v1.0.1: fix temperature conversion for negative values`

## Releases
- To push a new version to HACS, a **git tag + GitHub release** must be created:
  ```bash
  git tag vX.Y.Z
  git push && git push --tags
  gh release create vX.Y.Z --title "vX.Y.Z" --notes "changelog here"
  ```
- The tag version MUST match the version in `manifest.json`
- HACS uses tags/releases to detect available versions

## Version Bump Checklist
1. Update `version` in `custom_components/comet_wifi/manifest.json`
2. Commit with version prefix: `vX.Y.Z: description`
3. Create tag: `git tag vX.Y.Z`
4. Push: `git push && git push --tags`
5. Create GitHub release: `gh release create vX.Y.Z --title "vX.Y.Z" --notes "..."`

## Tech Stack
- Python (Home Assistant custom component)
- MQTT (via HA's built-in mqtt integration)
- Config Flow UI (no YAML needed)
- HACS compatible (custom repository)

## Architecture
```
custom_components/comet_wifi/
├── __init__.py       - Entry setup, platform forwarding
├── coordinator.py    - CometWifiDevice: MQTT subscribe/publish/polling
├── config_flow.py    - Auto-discovery + manual config flow
├── climate.py        - Climate entity (target/current temp)
├── sensor.py         - 11 sensor entities (battery, RSSI, valve, etc.)
├── switch.py         - 3 switches (keylock, rotate, summer) with R/M/W
├── number.py         - 4 number entities (offset, comfort temp, WOD settings)
├── button.py         - Refresh button (manual poll)
├── const.py          - All constants, register names, flags
├── manifest.json     - Integration metadata + version
├── strings.json      - English strings
└── translations/     - de.json, en.json
```

## MQTT Protocol (Eurotronic Comet WiFi)

### Topic Structure
```
{prefix}/{account_id}/{device_id}/S/{register}  → SET (write to device)
{prefix}/{account_id}/{device_id}/V/{register}  → VALUE (response from device)
```
- prefix: usually "02"
- account_id: 8-char hex (also MQTT username)
- device_id: MAC without colons (12-char hex)

### Device Behavior
- Battery-powered → does NOT publish proactively
- Must be POLLED via S/AF to get values
- After setting a value, poll again (2s delay) for confirmation
- Do NOT use retain=True on set commands (causes stale commands on reconnect)
- MQTT brokers: mqtt.eurotronic.io, mqtt1.eurotronic.io, mqtt3.eurotronic.io

### Complete Register Map

#### Writable Registers (implemented)
| Reg | Entity | Format | Notes |
|-----|--------|--------|-------|
| A0 | climate | `#XX` (hex/2=°C) | Target temp, range 4-28°C |
| A2 | number | `#XX` (signed/2=°C) | Offset, range -3 to +3°C |
| A3 | switch | `#XXYY00` (formula) | Flags bitfield, read-modify-write |
| A5 | number | `#XXYY` (°C, min) | Window-open: sensitivity + duration |
| A6 | number | `#XX` (hex/2=°C) | Comfort temperature |
| AF | button | `#FFFFFFFF` | Poll all registers |

#### Read-Only Registers (implemented as sensors)
| Reg | Format | Description |
|-----|--------|-------------|
| A1 | `#XX` (hex/2=°C) | Current temperature |
| A4 | `#XXYYZZZZ` | Heating profile state (byte0=mode: 0=off,1=manual,2=auto) |
| B1 | ASCII hex | Device name |
| B2 | ASCII hex | Firmware version |
| B3 | `#-XX` | WiFi RSSI (dBm) |
| B6 | 10 bytes | Network info (bytes1-4=IP) |
| BA | MAC text | Router BSSID |
| BD | `#XXYY` | Battery (byte0=level 0-8, 8=full→100%) |
| BE | `#XXYYZZ` | Valve/motor (byte1=position 0-100%) |

#### Writable but NOT YET implemented
| Reg | Format | Description |
|-----|--------|-------------|
| A7 | 8 bytes | Holiday profile (FFFFFFFFFFFFFFFF=off). Date format unknown. |
| A8-AE | variable | Weekly schedule (7 days). Slot format unknown. |

#### Unknown/Internal Registers
| Reg | Value | Notes |
|-----|-------|-------|
| B0 | `#U000000000000` | Device identifier |
| B4 | `#00000000` | Possibly error counter (always 0) |
| B5 | `#FF` | Unknown (max/disabled?) |
| B6 bytes5-9 | varies | Additional network params (unclear encoding) |
| B7 | `#00` | Unknown boolean/counter |
| BB | `#00` | Unknown |
| BC | `#FF` | Unknown |
| BD byte2 | `#00` when full | Unknown battery sub-field |
| BF | ASCII hex | WiFi security string (e.g. "[WPA2-PSK+SAE-CCM][WPS][ESS]") |

### A3 Register Encoding (IMPORTANT!)

**Reading:** `byte0 & 0x07` = flags
- Bit 0 (0x01): Summer mode
- Bit 1 (0x02): Display rotation
- Bit 2 (0x04): Keylock

**Writing:** 3-byte payload with formula:
```python
flags = desired_state  # combination of bit0, bit1, bit2
byte0 = 0x20 | flags
byte1 = (~flags) & 0x07
byte2 = 0x00
payload = f"#{byte0:02X}{byte1:02X}00"
```

**All possible SET payloads:**
| Payload | Summer | Rotate | Keylock |
|---------|--------|--------|---------|
| #200700 | OFF | OFF | OFF |
| #210600 | ON | OFF | OFF |
| #220500 | OFF | ON | OFF |
| #230400 | ON | ON | OFF |
| #240300 | OFF | OFF | ON |
| #250200 | ON | OFF | ON |
| #260100 | OFF | ON | ON |
| #270000 | ON | ON | ON |

**Implementation uses read-modify-write:** Read current flags, toggle specific bit, write back.

### Temperature Encoding
```python
# Hex to °C
temp_celsius = int(hex_value[1:3], 16) / 2

# °C to hex
hex_payload = f"#{int(temp * 2):02X}"
```

### A5 Window-Open Detection
```
#XXYY → XX = temperature drop threshold (°C), YY = duration (minutes)
APK limits: sensitivity 1-5°C, duration 5-30 min
```

### Polling
```
S/AF ← #FFFFFFFF    → device responds with ALL registers on V/* topics
S/AF ← #02000000    → device responds with A0, A1 only
```

## Config Flow
- Auto-discovery: subscribes to `#` (all topics), waits 30s, polls existing configured devices
- Manual: direct entry of prefix/account_id/device_id
- If no devices found: shows retry/manual choice dialog
- Translation note: HA uses `{variable}` as formatjs placeholders → NEVER use curly braces in description text unless providing `description_placeholders`

## Testing Environment
- HA: 192.168.2.10 (RPi 3, HAOS 17.3, Core 2026.5.2)
- Test thermostat: 192.168.2.101, MAC D43D395938CE, Account 000154A4
- DNS: AdGuard Home with DNS rewrite *.eurotronic.io → 192.168.2.10
- MQTT: Mosquitto broker with user=000154A4, pass=9D9CB2C82E445114

## APK Reverse Engineering (Smart Living 2.0 v1.4.6)
- Flutter/Dart app (AOT compiled → libapp.so, not easily decompiled)
- Key source paths found via strings:
  - `thermostat_attributes/flags.dart` → ThermostatFlags (A3)
  - `thermostat_attributes/holiday_profile.dart` → Holiday (A7)
  - `thermostat_attributes/window_open_detection.dart` → WOD (A5)
  - `thermostat_settings/offset_mapping/offset_mapping.dart` → Offset (A2)
  - `mqtt_treiber/send_time_schedule/` → Schedule (A8-AE)
  - `converter/hetaing_profile_schedule_to_mqtt.dart` → Schedule format
- Ghidra project at /tmp/ghidra-project/eurotronic (can open for manual analysis)
- Key classes: ThermostatFlags, HexBinConverter, MqttTopicBuilder, WindowOpenDetectionHelper, HeatingtimeCalculatorHelper, MqttSendTimeScheduleHelper

## Known Issues / Limitations
- Thermostat has ~2s response delay after set commands (battery/sleep mode)
- Window-open detection values must be written together (#XXYY, can't set one independently)
- A4 schedule mode decoding is medium-confidence (byte0: 0=off, 1=manual, 2=auto)
- BE valve position decoding is high-confidence (99% when summer=ON = valve closed)
- Holiday (A7) and weekly schedule (A8-AE) formats are not fully decoded

## TODO / Future Features
- [ ] Holiday profile (A7) - decode date format, add service/entity
- [ ] Weekly schedule (A8-AE) - decode time slot format, add UI
- [ ] advancedKeyLock / keyLockPlus (found in APK, unknown register bits)
- [ ] Multiple thermostats per account testing
- [ ] Firmware update notifications
- [ ] HVAC modes (comfort/eco based on A6 vs separate eco temp register?)
