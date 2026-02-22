# growth-hacs
GROWTH - Home Assistant Custom Integration

Track your child's growth, clothing sizes, BMI, and body shape — all dynamically calculated in Home Assistant.

---

## Features

| Feature | Details |
|--------|---------|
| 📅 **Age** | Auto-calculated daily from birth date (years, months, days) |
| 📏 **EU Top Size** | Based on height (children) or chest (adults) |
| 👖 **EU Bottom Size** | Based on height (children) or waist (adults) |
| 👟 **EU Shoe Size** | Calculated from foot length in cm |
| ⚖️ **BMI** | Age-adjusted BMI with category label |
| 🫀 **Body Shape** | Hourglass / Pear / Apple / Rectangle / Inverted Triangle |
| 🔢 **Editable Number Entities** | Change measurements directly from the HA dashboard |

---

## Installation

### Option A: Manual

1. Copy the `growth/` folder into your HA `config/custom_components/` directory:
   ```
   config/
   └── custom_components/
       └── growth/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── coordinator.py
           ├── sensor.py
           ├── number.py
           ├── const.py
           ├── strings.json
           └── translations/
               └── en.json
   ```

2. Restart Home Assistant.

3. Go to **Settings → Devices & Services → Add Integration** → search for **GROWTH**.

### Option B: HACS

Add this repo as a custom HACS repository (Integration type), then install and restart.

---

## Configuration

When adding the integration, fill in:

| Field | Format | Example |
|-------|--------|---------|
| **Name** | Text | Erik |
| **Birth Date** | YYYY-MM-DD | 2020-09-29 |
| **Gender** | Male / Female | Male |
| **Height** | cm | 128.5 |
| **Weight** | kg | 22.6 |
| **Chest** | cm circumference | 63.0 |
| **Waist** | cm circumference | 55.0 |
| **Hip** | cm circumference | 59.0 |
| **Foot Length** | cm | 19.5 |

> Tip: You can update measurements any time via **Configure** (gear icon) on the integration card.

---

## Entities Created

For each child, the following entities are created under a single device:

### 📊 Sensors (read-only, auto-calculated)
- `sensor.growth_<name>_age` — e.g. `7y 3m 12d`
- `sensor.growth_<name>_bmi` — e.g. `16.2 kg/m²`
- `sensor.growth_<name>_bmi_category` — e.g. `normal`
- `sensor.growth_<name>_body_shape` — e.g. `hourglass`
- `sensor.growth_<name>_eu_top_size` — e.g. `128`
- `sensor.growth_<name>_eu_bottom_size` — e.g. `122`
- `sensor.growth_<name>_eu_shoe_size` — e.g. `32`
- `sensor.growth_<name>_height` — cm
- `sensor.growth_<name>_weight` — kg
- `sensor.growth_<name>_chest` — cm
- `sensor.growth_<name>_waist` — cm
- `sensor.growth_<name>_hip` — cm
- `sensor.growth_<name>_foot_length` — cm

### 🔢 Number Entities (editable from dashboard)
- `number.growth_<name>_height` 
- `number.growth_<name>_weight`
- `number.growth_<name>_chest`
- `number.growth_<name>_waist`
- `number.growth_<name>_hip`
- `number.growth_<name>_foot_length`

---

## Dynamic Updates

- **Age** recalculates every hour (catches birthday changes automatically)
- **Sizes/BMI/Body Shape** recalculate **immediately** when you change any number entity from the dashboard
- All data persists in Home Assistant config entries

---

## EU Size Charts Used

### Children's Top & Bottom (by height)
| Height (cm) | EU Size |
|------------|---------|
| ≤56 | 50 |
| ≤62 | 56 |
| ≤80 | 74 |
| ≤92 | 86 |
| ≤104 | 98 |
| ≤116 | 110 |
| ≤128 | 122 |
| ≤140 | 134 |
| ≤152 | 146 |
| ≤164 | 158 |
| ≤170 | 164 |

### EU Shoe Size (from foot length)
Formula: `EU = (foot_length_mm + 15) / 6.67`

---

## Example Dashboard Card

```yaml
type: entities
title: Erik's GROWTH Stats
entities:
  - sensor.growth_erik_age
  - sensor.growth_erik_eu_top_size
  - sensor.growth_erik_eu_bottom_size
  - sensor.growth_erik_eu_shoe_size
  - sensor.growth_erik_bmi
  - sensor.growth_erik_body_shape
  - type: divider
  - number.growth_erik_height
  - number.growth_erik_weight
  - number.growth_erik_chest
  - number.growth_erik_waist
  - number.growth_erik_hip
  - number.growth_erik_foot_length
```

---

## Multiple Children

Add the integration multiple times — once per child. Each gets its own device.

---

## BMI Categories (Children)

| BMI | Category |
|-----|----------|
| <13.5 | Severely Underweight |
| <14.5 | Underweight |
| <18.0 | Normal |
| <21.0 | Overweight |
| ≥21.0 | Obese |

> Adult thresholds (18+) use standard WHO values.

---

## Body Shapes

Determined by chest/waist/hip ratios and gender:
`hourglass` · `pear` · `apple` · `inverted_triangle` · `rectangle`
