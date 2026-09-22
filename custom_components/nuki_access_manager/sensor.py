from __future__ import annotations

from homeassistant.components.sensor import SensorEntity

from .entity import NukiAccessManagerEntity


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data["nuki_access_manager"][entry.entry_id]
    async_add_entities([AuthorizationOverviewSensor(manager)])


class AuthorizationOverviewSensor(NukiAccessManagerEntity, SensorEntity):
    _attr_name = "Berechtigungen"
    _attr_icon = "mdi:account-key"

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_authorization_overview"

    @property
    def native_value(self):
        return self.manager.authorization_count

    @property
    def extra_state_attributes(self):
        last = self.manager.last_backup
        return {
            "aktiv": self.manager.enabled_count,
            "inaktiv": self.manager.authorization_count - self.manager.enabled_count,
            "sicherungsstaende": len(self.manager.backups),
            "letzte_sicherung": last.get("created_at") if last else None,
            "hinweis": "PIN-Ziffern und API-Token werden nicht gespeichert.",
        }
