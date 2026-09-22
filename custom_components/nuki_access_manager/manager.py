from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    EDITABLE_FIELDS,
    MAX_BACKUPS,
    SECRET_FIELDS,
    STORE_KEY_PREFIX,
    STORE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


def _without_secrets(value: Any) -> Any:
    """Return a deep copy which can safely be stored and committed."""
    if isinstance(value, dict):
        return {
            key: _without_secrets(item)
            for key, item in value.items()
            if key not in SECRET_FIELDS and key.lower() not in {item.lower() for item in SECRET_FIELDS}
        }
    if isinstance(value, list):
        return [_without_secrets(item) for item in value]
    return deepcopy(value)


class NukiAccessManager:
    def __init__(self, hass: HomeAssistant, entry, nuki_entry) -> None:
        self.hass = hass
        self.entry = entry
        self.nuki_entry = nuki_entry
        self.coordinator = nuki_entry.runtime_data
        self.store = Store(
            hass,
            STORE_VERSION,
            f"{STORE_KEY_PREFIX}.{entry.entry_id}",
        )
        self.backups: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        stored = await self.store.async_load() or {}
        self.backups = stored.get("backups", [])[-MAX_BACKUPS:]

    def devices(self) -> dict:
        return (self.coordinator.data or {}).get("devices", {})

    def authorizations(self, device_id) -> dict:
        return self.devices().get(device_id, {}).get("web_auth", {})

    def all_authorizations(self):
        for device_id, device in self.devices().items():
            for auth_id, auth in device.get("web_auth", {}).items():
                yield device_id, auth_id, auth

    async def async_backup(self, reason: str = "Manuell") -> dict:
        snapshot_devices = []
        for device_id, device in self.devices().items():
            auths = device.get("web_auth", {})
            if not auths:
                continue
            snapshot_devices.append(
                {
                    "device_id": str(device_id),
                    "name": device.get("name", "Nuki"),
                    "authorizations": _without_secrets(list(auths.values())),
                }
            )
        snapshot = {
            "created_at": dt_util.utcnow().isoformat(),
            "reason": reason,
            "devices": snapshot_devices,
        }
        self.backups = (self.backups + [snapshot])[-MAX_BACKUPS:]
        await self.store.async_save({"backups": self.backups})
        return snapshot

    async def async_update_authorization(
        self, device_id, auth_id, changes: dict[str, Any]
    ) -> None:
        forbidden = set(changes) - EDITABLE_FIELDS
        if forbidden:
            raise HomeAssistantError(
                f"Diese Felder dürfen nicht geändert werden: {', '.join(sorted(forbidden))}"
            )
        auth = self.authorizations(device_id).get(auth_id)
        if auth is None:
            auth = self.authorizations(device_id).get(str(auth_id))
        if auth is None:
            raise HomeAssistantError("Die Nuki-Berechtigung wurde nicht gefunden.")

        await self.async_backup(f"Vor Änderung: {auth.get('name', auth_id)}")
        web_id = self.coordinator.web_id(device_id)
        await self.coordinator.api.web_update_auth(web_id, auth["id"], changes)
        await self.coordinator.async_request_refresh()

        fresh = self.authorizations(device_id).get(auth_id)
        if fresh is None:
            fresh = self.authorizations(device_id).get(str(auth_id), {})
        mismatches = {
            key: {"expected": expected, "received": fresh.get(key)}
            for key, expected in changes.items()
            if fresh.get(key) != expected
        }
        if mismatches:
            _LOGGER.warning(
                "Nuki did not confirm authorization update for %s: %s",
                auth_id,
                mismatches,
            )
            raise HomeAssistantError(
                "Nuki hat die Änderung noch nicht bestätigt. Der Sicherungsstand blieb erhalten."
            )

    async def async_create_keypad_authorization(
        self,
        device_id,
        *,
        name: str,
        code: int,
        rules: dict[str, Any] | None = None,
    ) -> None:
        code_text = str(code)
        if (
            len(code_text) != 6
            or "0" in code_text
            or code_text.startswith("12")
            or not code_text.isdigit()
        ):
            raise HomeAssistantError(
                "Der Keypad-Code muss aus 6 Ziffern von 1 bis 9 bestehen und darf nicht mit 12 beginnen."
            )
        await self.async_backup(f"Vor Anlage: {name}")
        payload = {
            "name": name,
            "type": 13,
            "code": int(code_text),
            "enabled": True,
            "remoteAllowed": True,
        }
        if rules:
            payload.update({key: value for key, value in rules.items() if key in EDITABLE_FIELDS})
        web_id = self.coordinator.web_id(device_id)
        api = self.coordinator.api
        await api.web_async_json(
            lambda request, headers: request.put(
                api.web_url(f"/smartlock/{web_id}/auth"),
                headers=headers,
                json=payload,
            )
        )
        # The code exists only in this local call frame and is never logged or stored.
        await self.coordinator.async_request_refresh()

    async def async_delete_authorization(self, device_id, auth_id) -> None:
        auth = self.authorizations(device_id).get(auth_id)
        if auth is None:
            auth = self.authorizations(device_id).get(str(auth_id))
        if auth is None:
            raise HomeAssistantError("Die Nuki-Berechtigung wurde nicht gefunden.")
        await self.async_backup(f"Vor Löschen: {auth.get('name', auth_id)}")
        web_id = self.coordinator.web_id(device_id)
        api = self.coordinator.api
        await api.web_async_json(
            lambda request, headers: request.delete(
                api.web_url(f"/smartlock/{web_id}/auth/{auth['id']}"),
                headers=headers,
            )
        )
        await self.coordinator.async_request_refresh()

    @property
    def authorization_count(self) -> int:
        return sum(1 for _ in self.all_authorizations())

    @property
    def enabled_count(self) -> int:
        return sum(1 for _, _, auth in self.all_authorizations() if auth.get("enabled"))

    @property
    def last_backup(self) -> dict | None:
        return self.backups[-1] if self.backups else None

    @staticmethod
    def daily_backup_interval() -> timedelta:
        return timedelta(days=1)
