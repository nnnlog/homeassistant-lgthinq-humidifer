"""Constants for the LG ThinQ Humidifier integration."""

DOMAIN = "lgthinqhumidifer"

# API URLs
LGE_AUTH_BASE_URL = "https://kr.lid.lgemembers.com"
THINQ_API_BASE_URL = "https://kic-service.lgthinq.com:46030"

# Client IDs
# Client IDs are now generated dynamically in config_flow.py

# Common Headers
API_KEY = "VGhpblEyLjAgU0VSVklDRQ=="
APP_TYPE = "NUTS"
APP_LEVEL = "PRD"
APP_OS = "ANDROID"
SERVICE_CODE = "SVC202"
COUNTRY_CODE = "KR"
LANGUAGE_CODE = "ko-KR"
SERVICE_PHASE = "OP"
ORIGIN_MOBILE = "app-native"
ORIGIN_WEB = "app-web-ANDROID"
LOGIN_TYPE = "LGE"

# App Version Constants
APP_VERSION_HEADER = "LG ThinQ/5.1.20330"
THINQ_APP_VER = "5.1.2000"
USER_AGENT_MOBILE = "okhttp/4.12.0"
USER_AGENT_WEB = "Mozilla/5.0 (Linux; Android 16; Pixel 10 Pro Build/BD3A.251105.010.E1; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.135 Mobile Safari/537.36"

# Device Constants
DEVICE_TYPE_HUMIDIFIER = 404

# Operation Modes (airState.opMode)
OP_MODE_HUMIDIFY = 24
OP_MODE_HUMIDIFY_AIR_CLEAN = 12
OP_MODE_AIR_CLEAN = 5

MODE_TO_STR = {
    OP_MODE_HUMIDIFY: "가습",
    OP_MODE_HUMIDIFY_AIR_CLEAN: "가습청정",
    OP_MODE_AIR_CLEAN: "공기청정",
}

STR_TO_MODE = {v: k for k, v in MODE_TO_STR.items()}
