from __future__ import annotations

import voluptuous as vol

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_NUKI_ENTRY_ID, DOMAIN, PLATFORMS
from .manager import NukiAccessManager

SERVICE_BACKUP = "backup_now"
SERVICE_UPDATE = "update_authorization"
SERVICE_CREATE_KEYPAD = "create_keypad_authorization"
SERVICE_DELETE = "delete_authorization"


def _manager(hass: HomeAssistant, entry_id: str) -> NukiAccessManager:
    manager = hass.data.get(DOMAIN, {}).get(entry_id)
    if manager is None:
        raise HomeAssistantError("Die Nuki-Berechtigungsverwaltung ist nicht geladen.")
    return manager


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})

    async def backup(call: ServiceCall):
        await _manager(hass, call.data["entry_id"]).async_backup("Manuell")

    async def update(call: ServiceCall):
        changes = {
            key: call.data[key]
            for key in (
                "name",
                "enabled",
                "remoteAllowed",
                "allowedFromDate",
                "allowedUntilDate",
                "allowedWeekDays",
                "allowedFromTime",
                "allowedUntilTime",
            )
            if key in call.data
        }
        await _manager(hass, call.data["entry_id"]).async_update_authorization(
            call.data["device_id"], call.data["authorization_id"], changes
        )

    async def create_keypad(call: ServiceCall):
        await _manager(hass, call.data["entry_id"]).async_create_keypad_authorization(
            call.data["device_id"],
            name=call.data[CONF_NAME],
            code=call.data["code"],
        )

    async def delete(call: ServiceCall):
        await _manager(hass, call.data["entry_id"]).async_delete_authorization(
            call.data["device_id"], call.data["authorization_id"]
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_BACKUP,
        backup,
        schema=vol.Schema({vol.Required("entry_id"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE,
        update,
        schema=vol.Schema(
            {
                vol.Required("entry_id"): cv.string,
                vol.Required("device_id"): vol.Any(cv.string, int),
                vol.Required("authorization_id"): vol.Any(cv.string, int),
                vol.Optional("name"): cv.string,
                vol.Optional("enabled"): cv.boolean,
                vol.Optional("remoteAllowed"): cv.boolean,
                vol.Optional("allowedFromDate"): cv.string,
                vol.Optional("allowedUntilDate"): cv.string,
                vol.Optional("allowedWeekDays"): vol.Coerce(int),
                vol.Optional("allowedFromTime"): vol.Coerce(int),
                vol.Optional("allowedUntilTime"): vol.Coerce(int),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_KEYPAD,
        create_keypad,
        schema=vol.Schema(
            {
                vol.Required("entry_id"): cv.string,
                vol.Required("device_id"): vol.Any(cv.string, int),
                vol.Required(CONF_NAME): cv.string,
                vol.Required("code"): vol.All(vol.Coerce(int), vol.Range(min=111111, max=999999)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE,
        delete,
        schema=vol.Schema(
            {
                vol.Required("entry_id"): cv.string,
                vol.Required("device_id"): vol.Any(cv.string, int),
                vol.Required("authorization_id"): vol.Any(cv.string, int),
            }
        ),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    nuki_entry = hass.config_entries.async_get_entry(entry.data[CONF_NUKI_ENTRY_ID])
    if nuki_entry is None or nuki_entry.runtime_data is None:
        raise ConfigEntryNotReady("Die Nuki-Integration ist noch nicht bereit.")

    manager = NukiAccessManager(hass, entry, nuki_entry)
    await manager.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    if not manager.backups:
        await manager.async_backup("Erste Übernahme")

    async def daily_backup(_now):
        await manager.async_backup("Tägliche Sicherung")

    entry.async_on_unload(
        async_track_time_interval(hass, daily_backup, manager.daily_backup_interval())
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
