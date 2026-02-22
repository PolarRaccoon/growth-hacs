"""Number entities for GROWTH - allows editing measurements from HA UI/dashboards."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CHEST,
    CONF_FOOT_LENGTH,
    CONF_HEIGHT,
    CONF_HIP,
    CONF_NAME,
    CONF_WAIST,
    CONF_WEIGHT,
    DOMAIN,
)
from .coordinator import GrowthDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class GrowthNumberEntityDescription(NumberEntityDescription):
    """Extended number description."""
    conf_key: str = ""
    data_key: str = ""


NUMBER_DESCRIPTIONS: tuple[GrowthNumberEntityDescription, ...] = (
    GrowthNumberEntityDescription(
        key="height_input",
        name="Height",
        icon="mdi:human-male-height",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        native_min_value=30,
        native_max_value=220,
        native_step=0.5,
        mode=NumberMode.BOX,
        conf_key=CONF_HEIGHT,
        data_key="height",
    ),
    GrowthNumberEntityDescription(
        key="weight_input",
        name="Weight",
        icon="mdi:weight-kilogram",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        native_min_value=1,
        native_max_value=200,
        native_step=0.1,
        mode=NumberMode.BOX,
        conf_key=CONF_WEIGHT,
        data_key="weight",
    ),
    GrowthNumberEntityDescription(
        key="chest_input",
        name="Chest",
        icon="mdi:human",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        native_min_value=20,
        native_max_value=200,
        native_step=0.5,
        mode=NumberMode.BOX,
        conf_key=CONF_CHEST,
        data_key="chest",
    ),
    GrowthNumberEntityDescription(
        key="waist_input",
        name="Waist",
        icon="mdi:human-male-height-variant",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        native_min_value=20,
        native_max_value=200,
        native_step=0.5,
        mode=NumberMode.BOX,
        conf_key=CONF_WAIST,
        data_key="waist",
    ),
    GrowthNumberEntityDescription(
        key="hip_input",
        name="Hip",
        icon="mdi:human",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        native_min_value=20,
        native_max_value=200,
        native_step=0.5,
        mode=NumberMode.BOX,
        conf_key=CONF_HIP,
        data_key="hip",
    ),
    GrowthNumberEntityDescription(
        key="foot_length_input",
        name="Foot Length",
        icon="mdi:shoe-print",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        native_min_value=8,
        native_max_value=35,
        native_step=0.1,
        mode=NumberMode.BOX,
        conf_key=CONF_FOOT_LENGTH,
        data_key="foot_length",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GROWTH number entities."""
    coordinator: GrowthDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        GrowthNumberEntity(coordinator, entry, description)
        for description in NUMBER_DESCRIPTIONS
    )


class GrowthNumberEntity(CoordinatorEntity[GrowthDataUpdateCoordinator], NumberEntity):
    """Editable number entity for GROWTH measurements.
    
    When a value is set, it updates the config entry options so it persists
    and triggers coordinator refresh to recalculate all derived sensors.
    """

    entity_description: GrowthNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GrowthDataUpdateCoordinator,
        entry: ConfigEntry,
        description: GrowthNumberEntityDescription,
    ) -> None:
        """Initialize number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        child_name = entry.data.get(CONF_NAME, "child")
        slug = child_name.lower().replace(" ", "_")
        self._attr_unique_id = f"growth_{slug}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"GROWTH: {child_name}",
            manufacturer="GROWTH Integration",
            model="Child Size Tracker",
        )

    @property
    def native_value(self) -> float | None:
        """Return current value from coordinator data."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self.entity_description.data_key, 0)
        return float(value) if value else None

    async def async_set_native_value(self, value: float) -> None:
        """Update the measurement and trigger recalculation."""
        # Merge existing options with the new value
        new_options = {
            **self._entry.data,
            **self._entry.options,
            self.entity_description.conf_key: value,
        }
        # Update config entry options - this triggers async_update_options in __init__.py
        self.hass.config_entries.async_update_entry(
            self._entry,
            options=new_options,
        )
        # Explicitly request coordinator refresh to update sensors immediately
        await self.coordinator.async_request_refresh()
