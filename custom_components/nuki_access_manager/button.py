from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .entity import NukiAccessManagerEntity


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data["nuki_access_manager"][entry.entry_id]
    async_add_entities([BackupNowButton(manager)])


class BackupNowButton(NukiAccessManagerEntity, ButtonEntity):
    _attr_name = "Berechtigungen jetzt sichern"
    _attr_icon = "mdi:content-save"

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_backup_now"

    async def async_press(self) -> None:
        await self.manager.async_backup("Manuell über Schaltfläche")
