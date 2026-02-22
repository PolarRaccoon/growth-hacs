"""Config flow for GROWTH integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_BIRTH_DATE,
    CONF_CHEST,
    CONF_FOOT_LENGTH,
    CONF_GENDER,
    CONF_HEIGHT,
    CONF_HIP,
    CONF_NAME,
    CONF_WAIST,
    CONF_WEIGHT,
    DOMAIN,
    GENDER_FEMALE,
    GENDER_MALE,
)

_LOGGER = logging.getLogger(__name__)


def _build_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=d.get(CONF_NAME, "")): str,
            vol.Required(CONF_BIRTH_DATE, default=d.get(CONF_BIRTH_DATE, "")): str,
            vol.Required(CONF_GENDER, default=d.get(CONF_GENDER, GENDER_MALE)): vol.In(
                [GENDER_MALE, GENDER_FEMALE]
            ),
            vol.Optional(CONF_HEIGHT, default=d.get(CONF_HEIGHT, 0)): vol.Coerce(float),
            vol.Optional(CONF_WEIGHT, default=d.get(CONF_WEIGHT, 0)): vol.Coerce(float),
            vol.Optional(CONF_CHEST, default=d.get(CONF_CHEST, 0)): vol.Coerce(float),
            vol.Optional(CONF_WAIST, default=d.get(CONF_WAIST, 0)): vol.Coerce(float),
            vol.Optional(CONF_HIP, default=d.get(CONF_HIP, 0)): vol.Coerce(float),
            vol.Optional(CONF_FOOT_LENGTH, default=d.get(CONF_FOOT_LENGTH, 0)): vol.Coerce(float),
        }
    )


class GrowthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GROWTH."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate birth date
            birth_date = user_input.get(CONF_BIRTH_DATE, "")
            if not self._validate_date(birth_date):
                errors[CONF_BIRTH_DATE] = "invalid_date"
            else:
                name = user_input[CONF_NAME].strip()
                if not name:
                    errors[CONF_NAME] = "name_required"
                else:
                    await self.async_set_unique_id(f"growth_{name.lower().replace(' ', '_')}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"GROWTH: {name}",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(),
            errors=errors,
            description_placeholders={
                "date_format": "YYYY-MM-DD",
            },
        )

    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """Validate ISO date string."""
        try:
            from datetime import date
            date.fromisoformat(date_str)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> GrowthOptionsFlow:
        """Return options flow."""
        return GrowthOptionsFlow(config_entry)


class GrowthOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow - update measurements."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options update."""
        errors: dict[str, str] = {}

        # Merge current data + options to get latest values
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            birth_date = user_input.get(CONF_BIRTH_DATE, "")
            if not GrowthConfigFlow._validate_date(birth_date):
                errors[CONF_BIRTH_DATE] = "invalid_date"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(current),
            errors=errors,
            description_placeholders={
                "date_format": "YYYY-MM-DD",
                "child_name": current.get(CONF_NAME, "child"),
            },
        )
