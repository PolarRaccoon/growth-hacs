"""Sensor entities for GROWTH integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME
from .coordinator import GrowthDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class GrowthSensorEntityDescription(SensorEntityDescription):
    """Extended sensor description for GROWTH."""
    data_key: str = ""
    icon_func: Any = None  # callable(data) -> icon


SENSOR_DESCRIPTIONS: tuple[GrowthSensorEntityDescription, ...] = (
    GrowthSensorEntityDescription(
        key="age",
        name="Age",
        icon="mdi:cake-variant",
        data_key="age_display",
    ),
    GrowthSensorEntityDescription(
        key="bmi",
        name="BMI",
        icon="mdi:scale-bathroom",
        native_unit_of_measurement="kg/m²",
        state_class=SensorStateClass.MEASUREMENT,
        data_key="bmi",
    ),
    GrowthSensorEntityDescription(
        key="bmi_category",
        name="BMI Category",
        icon="mdi:human",
        data_key="bmi_category",
    ),
    GrowthSensorEntityDescription(
        key="body_shape",
        name="Body Shape",
        icon="mdi:human-handsdown",
        data_key="body_shape",
    ),
    GrowthSensorEntityDescription(
        key="eu_top",
        name="EU Top Size",
        icon="mdi:tshirt-crew",
        data_key="eu_top",
    ),
    GrowthSensorEntityDescription(
        key="eu_bottom",
        name="EU Bottom Size",
        icon="mdi:hanger",
        data_key="eu_bottom",
    ),
    GrowthSensorEntityDescription(
        key="eu_shoe",
        name="EU Shoe Size",
        icon="mdi:shoe-sneaker",
        data_key="eu_shoe",
    ),
    GrowthSensorEntityDescription(
        key="height",
        name="Height",
        icon="mdi:human-male-height",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        data_key="height",
    ),
    GrowthSensorEntityDescription(
        key="weight",
        name="Weight",
        icon="mdi:weight-kilogram",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        data_key="weight",
    ),
    GrowthSensorEntityDescription(
        key="chest",
        name="Chest",
        icon="mdi:human",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        data_key="chest",
    ),
    GrowthSensorEntityDescription(
        key="waist",
        name="Waist",
        icon="mdi:human-male-height-variant",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        data_key="waist",
    ),
    GrowthSensorEntityDescription(
        key="hip",
        name="Hip",
        icon="mdi:human",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        data_key="hip",
    ),
    GrowthSensorEntityDescription(
        key="foot_length",
        name="Foot Length",
        icon="mdi:shoe-print",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        data_key="foot_length",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GROWTH sensors."""
    coordinator: GrowthDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        GrowthSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class GrowthSensor(CoordinatorEntity[GrowthDataUpdateCoordinator], SensorEntity):
    """Represent a GROWTH sensor."""

    entity_description: GrowthSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GrowthDataUpdateCoordinator,
        entry: ConfigEntry,
        description: GrowthSensorEntityDescription,
    ) -> None:
        """Initialize sensor."""
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
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self.entity_description.data_key)
        if value == 0 and self.entity_description.data_key in (
            "height", "weight", "chest", "waist", "hip", "foot_length"
        ):
            return None  # Don't show 0 for measurements
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for main size sensors."""
        data = self.coordinator.data or {}
        if self.entity_description.key == "eu_top":
            return {
                "height_cm": data.get("height"),
                "chest_cm": data.get("chest"),
                "age_years": data.get("age_years"),
            }
        if self.entity_description.key == "eu_bottom":
            return {
                "height_cm": data.get("height"),
                "waist_cm": data.get("waist"),
                "hip_cm": data.get("hip"),
                "age_years": data.get("age_years"),
            }
        if self.entity_description.key == "eu_shoe":
            return {
                "foot_length_cm": data.get("foot_length"),
            }
        if self.entity_description.key == "bmi":
            return {
                "category": data.get("bmi_category"),
                "height_cm": data.get("height"),
                "weight_kg": data.get("weight"),
            }
        if self.entity_description.key == "body_shape":
            return {
                "chest_cm": data.get("chest"),
                "waist_cm": data.get("waist"),
                "hip_cm": data.get("hip"),
                "gender": data.get("gender"),
            }
        if self.entity_description.key == "age":
            return {
                "years": data.get("age_years"),
                "months": data.get("age_months"),
                "days": data.get("age_days"),
                "birth_date": data.get("birth_date"),
            }
        return {}
