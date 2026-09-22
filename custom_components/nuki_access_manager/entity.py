from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class NukiAccessManagerEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, manager) -> None:
        super().__init__(manager.coordinator)
        self.manager = manager
        self._attr_device_info = {
            "identifiers": {(DOMAIN, manager.entry.entry_id)},
            "name": "Nuki Berechtigungen",
            "manufacturer": "Nuki",
            "model": "Lokale Berechtigungssicherung",
        }


class NukiAuthorizationEntity(NukiAccessManagerEntity):
    def __init__(self, manager, device_id, auth_id) -> None:
        super().__init__(manager)
        self.device_id = device_id
        self.auth_id = auth_id

    @property
    def auth(self) -> dict:
        auths = self.manager.authorizations(self.device_id)
        return auths.get(self.auth_id) or auths.get(str(self.auth_id)) or {}

    @property
    def available(self) -> bool:
        return bool(self.auth) and super().available

    @property
    def auth_name(self) -> str:
        return self.auth.get("name", str(self.auth_id))
