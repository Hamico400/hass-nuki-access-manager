from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import NukiAuthorizationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data["nuki_access_manager"][entry.entry_id]
    async_add_entities(
        AuthorizationRemoteAccess(manager, device_id, auth_id)
        for device_id, auth_id, _auth in manager.all_authorizations()
    )


class AuthorizationRemoteAccess(NukiAuthorizationEntity, SwitchEntity):
    _attr_icon = "mdi:cloud-key"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, manager, device_id, auth_id):
        super().__init__(manager, device_id, auth_id)
        self._attr_unique_id = (
            f"{manager.entry.entry_id}_{device_id}_{auth_id}_remote_allowed"
        )
        self._attr_name = f"{self.auth_name} – Fernzugriff"

    @property
    def is_on(self):
        return self.auth.get("remoteAllowed", False)

    async def async_turn_on(self, **kwargs):
        await self.manager.async_update_authorization(
            self.device_id, self.auth_id, {"remoteAllowed": True}
        )

    async def async_turn_off(self, **kwargs):
        await self.manager.async_update_authorization(
            self.device_id, self.auth_id, {"remoteAllowed": False}
        )
