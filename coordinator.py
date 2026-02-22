"""Data coordinator for GROWTH integration."""
from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class GrowthDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage GROWTH data and calculations."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_NAME]}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and calculate all data."""
        data = {**self.entry.data, **self.entry.options}
        return self._calculate_all(data)

    def _calculate_all(self, data: dict[str, Any]) -> dict[str, Any]:
        """Run all calculations."""
        result: dict[str, Any] = {}

        # Basic info
        birth_date_str = data.get(CONF_BIRTH_DATE, "")
        gender = data.get(CONF_GENDER, "")
        height = float(data.get(CONF_HEIGHT, 0) or 0)
        weight = float(data.get(CONF_WEIGHT, 0) or 0)
        chest = float(data.get(CONF_CHEST, 0) or 0)
        waist = float(data.get(CONF_WAIST, 0) or 0)
        hip = float(data.get(CONF_HIP, 0) or 0)
        foot_length = float(data.get(CONF_FOOT_LENGTH, 0) or 0)

        # Age calculation
        age_years, age_months, age_days = self._calc_age(birth_date_str)
        result["age_years"] = age_years
        result["age_months"] = age_months
        result["age_days"] = age_days
        result["age_display"] = self._format_age(age_years, age_months, age_days)

        # BMI
        bmi, bmi_category = self._calc_bmi(height, weight, age_years, gender)
        result["bmi"] = bmi
        result["bmi_category"] = bmi_category

        # Body shape
        result["body_shape"] = self._calc_body_shape(chest, waist, hip, gender)

        # EU Sizes
        result["eu_top"] = self._calc_eu_top(height, chest, age_years)
        result["eu_bottom"] = self._calc_eu_bottom(height, waist, hip, age_years)
        result["eu_shoe"] = self._calc_eu_shoe(foot_length)

        # Raw measurements stored for reference
        result["height"] = height
        result["weight"] = weight
        result["chest"] = chest
        result["waist"] = waist
        result["hip"] = hip
        result["foot_length"] = foot_length
        result["gender"] = gender
        result["birth_date"] = birth_date_str
        result["name"] = data.get(CONF_NAME, "")

        return result

    def _calc_age(self, birth_date_str: str) -> tuple[int, int, int]:
        """Calculate age in years, months, days."""
        if not birth_date_str:
            return 0, 0, 0
        try:
            birth_date = date.fromisoformat(birth_date_str)
            today = date.today()
            years = today.year - birth_date.year
            months = today.month - birth_date.month
            days = today.day - birth_date.day
            if days < 0:
                months -= 1
                # Days in previous month
                prev_month = today.month - 1 if today.month > 1 else 12
                prev_year = today.year if today.month > 1 else today.year - 1
                days_in_prev = (date(prev_year, prev_month % 12 + 1, 1) - timedelta(days=1)).day if prev_month != 12 else 31
                days += days_in_prev
            if months < 0:
                years -= 1
                months += 12
            return max(0, years), max(0, months), max(0, days)
        except (ValueError, TypeError):
            return 0, 0, 0

    def _format_age(self, years: int, months: int, days: int) -> str:
        """Format age as human-readable string."""
        parts = []
        if years > 0:
            parts.append(f"{years}y")
        if months > 0:
            parts.append(f"{months}m")
        if days > 0 or not parts:
            parts.append(f"{days}d")
        return " ".join(parts)

    def _calc_bmi(self, height_cm: float, weight_kg: float, age: int, gender: str) -> tuple[float | None, str]:
        """Calculate BMI and category (age-adjusted for children)."""
        if height_cm <= 0 or weight_kg <= 0:
            return None, "unknown"
        height_m = height_cm / 100
        bmi = round(weight_kg / (height_m ** 2), 1)

        # Child BMI categories (simplified WHO/CDC percentile-based)
        if age < 2:
            category = "infant"
        elif age < 18:
            # Approximate child BMI categories
            if bmi < 13.5:
                category = "severely_underweight"
            elif bmi < 14.5:
                category = "underweight"
            elif bmi < 18.0:
                category = "normal"
            elif bmi < 21.0:
                category = "overweight"
            else:
                category = "obese"
        else:
            if bmi < 18.5:
                category = "underweight"
            elif bmi < 25.0:
                category = "normal"
            elif bmi < 30.0:
                category = "overweight"
            else:
                category = "obese"

        return bmi, category

    def _calc_body_shape(self, chest: float, waist: float, hip: float, gender: str) -> str:
        """Determine body shape based on measurements."""
        if chest <= 0 or waist <= 0 or hip <= 0:
            return "unknown"

        is_female = gender == GENDER_FEMALE

        # Ratios
        waist_hip = waist / hip if hip > 0 else 0
        waist_chest = waist / chest if chest > 0 else 0
        chest_hip_diff = abs(chest - hip)

        if is_female:
            if waist_hip < 0.75 and chest_hip_diff < 5:
                return "hourglass"
            elif hip > chest + 5 and waist_hip < 0.80:
                return "pear"
            elif chest > hip + 5:
                return "inverted_triangle"
            elif waist_hip >= 0.85:
                return "apple"
            else:
                return "rectangle"
        else:
            if chest > waist + 10 and chest > hip:
                return "inverted_triangle"
            elif waist >= chest * 0.9 and waist >= hip * 0.9:
                return "apple"
            elif hip > chest + 5:
                return "pear"
            elif abs(chest - hip) < 5 and waist < chest * 0.9:
                return "hourglass"
            else:
                return "rectangle"

    def _calc_eu_top(self, height_cm: float, chest_cm: float, age: int) -> str:
        """Calculate EU top/shirt size."""
        # Children's EU top sizes based on height
        if height_cm > 0 and age < 16:
            # EU children's sizes follow height bands
            child_top_map = [
                (56, "50"), (62, "56"), (68, "62"), (74, "68"),
                (80, "74"), (86, "80"), (92, "86"), (98, "92"),
                (104, "98"), (110, "104"), (116, "110"), (122, "116"),
                (128, "122"), (134, "128"), (140, "134"), (146, "140"),
                (152, "146"), (158, "152"), (164, "158"), (170, "164"),
            ]
            for max_height, size in child_top_map:
                if height_cm <= max_height:
                    return size
            # Fallback to chest-based adult sizing
        # Adult EU top based on chest
        if chest_cm > 0:
            adult_chest_map = [
                (84, "XS (34)"), (88, "S (36)"), (92, "S (38)"),
                (96, "M (40)"), (100, "M (42)"), (104, "L (44)"),
                (108, "L (46)"), (112, "XL (48)"), (116, "XL (50)"),
                (120, "XXL (52)"), (124, "XXL (54)"), (128, "3XL (56)"),
            ]
            for max_chest, size in adult_chest_map:
                if chest_cm <= max_chest:
                    return size
            return "3XL+"
        if height_cm > 0:
            return f"~{int(height_cm)} height"
        return "unknown"

    def _calc_eu_bottom(self, height_cm: float, waist_cm: float, hip_cm: float, age: int) -> str:
        """Calculate EU bottom/trouser size."""
        if height_cm > 0 and age < 16:
            child_bottom_map = [
                (56, "50"), (62, "56"), (68, "62"), (74, "68"),
                (80, "74"), (86, "80"), (92, "86"), (98, "92"),
                (104, "98"), (110, "104"), (116, "110"), (122, "116"),
                (128, "122"), (134, "128"), (140, "134"), (146, "140"),
                (152, "146"), (158, "152"), (164, "158"), (170, "164"),
            ]
            for max_height, size in child_bottom_map:
                if height_cm <= max_height:
                    return size

        # Adult EU trouser size based on waist
        if waist_cm > 0:
            # EU waist sizes (approx waist / 2 = EU size)
            eu_size = round(waist_cm / 2) * 2  # round to even
            return str(eu_size)
        if height_cm > 0:
            return f"~{int(height_cm)} height"
        return "unknown"

    def _calc_eu_shoe(self, foot_length_cm: float) -> str:
        """Calculate EU shoe size from foot length in cm."""
        if foot_length_cm <= 0:
            return "unknown"
        # EU shoe size formula: foot_length_cm * 3 / 2 (Paris points)
        # More precise: (foot_length_mm + 15) / 6.67
        foot_mm = foot_length_cm * 10
        eu_size = (foot_mm + 15) / 6.67
        eu_rounded = round(eu_size * 2) / 2  # round to nearest 0.5

        # Map to standard EU sizes
        if eu_rounded <= 16:
            return "16"
        elif eu_rounded >= 50:
            return "50+"
        # Return as integer if .0, else with .5
        if eu_rounded == int(eu_rounded):
            return str(int(eu_rounded))
        return str(eu_rounded)
