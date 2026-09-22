from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import NukiAuthorizationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data["nuki_access_manager"][entry.entry_id]
    async_add_entities(
        AuthorizationName(manager, device_id, auth_id)
        for device_id, auth_id, _auth in manager.all_authorizations()
    )


class AuthorizationName(NukiAuthorizationEntity, TextEntity):
    _attr_name = "Name"
    _attr_icon = "mdi:account-edit"
    _attr_native_min = 1
    _attr_native_max = 32
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, manager, device_id, auth_id):
        super().__init__(manager, device_id, auth_id)
        self._attr_unique_id = (
            f"{manager.entry.entry_id}_{device_id}_{auth_id}_authorization_name"
        )
        self._attr_name = f"{self.auth_name} – Name"

    @property
    def native_value(self):
        return self.auth_name

    async def async_set_value(self, value: str) -> None:
        await self.manager.async_update_authorization(
            self.device_id, self.auth_id, {"name": value.strip()}
        )
