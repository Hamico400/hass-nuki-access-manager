from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_NUKI_ENTRY_ID, DOMAIN


class NukiAccessManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        nuki_entries = self.hass.config_entries.async_entries("nuki_ng")
        if not nuki_entries:
            return self.async_abort(reason="nuki_not_configured")

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NUKI_ENTRY_ID])
            self._abort_if_unique_id_configured()
            source = self.hass.config_entries.async_get_entry(
                user_input[CONF_NUKI_ENTRY_ID]
            )
            return self.async_create_entry(
                title=f"Nuki Berechtigungen – {source.title if source else 'Nuki'}",
                data=user_input,
            )

        options = {entry.entry_id: entry.title for entry in nuki_entries}
        schema = vol.Schema(
            {
                vol.Required(CONF_NUKI_ENTRY_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=key, label=value)
                            for key, value in options.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NukiAccessManagerOptionsFlow()


class NukiAccessManagerOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        return self.async_create_entry(title="", data={})
