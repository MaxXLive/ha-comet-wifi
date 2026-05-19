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
REG_HOLIDAY = "A7"
REG_BATTERY = "BD"
REG_POLL = "AF"
REG_VERIFY = "XX"

# A3 option payloads
PAYLOAD_KEYLOCK_ON = "#270000"
PAYLOAD_KEYLOCK_OFF = "#230400"
PAYLOAD_ROTATE_ON = "#220500"
PAYLOAD_ROTATE_OFF = "#200700"
PAYLOAD_SUMMER_ON = "#230400"
PAYLOAD_SUMMER_OFF = "#220500"

# Poll payloads
PAYLOAD_POLL_ALL = "#0b"
PAYLOAD_POLL_TEMP = "#02000000"

PLATFORMS = ["climate", "sensor", "switch", "button"]
