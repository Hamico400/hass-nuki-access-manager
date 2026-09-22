DOMAIN = "nuki_access_manager"
PLATFORMS = ["sensor", "text", "switch", "button"]

CONF_NUKI_ENTRY_ID = "nuki_entry_id"

STORE_VERSION = 1
STORE_KEY_PREFIX = "nuki_access_manager"
MAX_BACKUPS = 90

SECRET_FIELDS = {
    "code",
    "pin",
    "pinCode",
    "token",
    "webToken",
}

EDITABLE_FIELDS = {
    "name",
    "enabled",
    "remoteAllowed",
    "allowedFromDate",
    "allowedUntilDate",
    "allowedWeekDays",
    "allowedFromTime",
    "allowedUntilTime",
}
