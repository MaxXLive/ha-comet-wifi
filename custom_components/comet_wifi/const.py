"""Constants for the Comet WiFi Thermostat integration."""

DOMAIN = "comet_wifi"
MANUFACTURER = "Eurotronic"
MODEL = "Comet WiFi"

CONF_TOPIC_PREFIX = "topic_prefix"
CONF_ACCOUNT_ID = "account_id"
CONF_DEVICE_ID = "device_id"
CONF_POLL_INTERVAL = "poll_interval"

DEFAULT_PREFIX = "02"
DEFAULT_POLL_INTERVAL = 30

# MQTT registers
REG_TARGET_TEMP = "A0"
REG_CURRENT_TEMP = "A1"
REG_TEMP_OFFSET = "A2"
REG_OPTIONS = "A3"
REG_WINDOW_OPEN = "A5"
REG_COMFORT_TEMP = "A6"
REG_HOLIDAY = "A7"
REG_BATTERY = "BD"
REG_POLL = "AF"
REG_VERIFY = "XX"

# A3 flags bitfield (byte0 & 0x07)
FLAG_SUMMER = 0x01   # bit 0
FLAG_ROTATE = 0x02   # bit 1
FLAG_KEYLOCK = 0x04  # bit 2

# Poll payloads
PAYLOAD_POLL_ALL = "#FFFFFFFF"
PAYLOAD_POLL_TEMP = "#02000000"

PLATFORMS = ["climate", "sensor", "switch", "button", "number"]
