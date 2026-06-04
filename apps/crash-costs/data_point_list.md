# Map and crash data points

## Hover pop-ups

### County level

- **[Primary metric]** (bold)
- Total crashes | Total people directly involved in crashes
- Number of fatalities | Number of injuries | Number of pedestrians or cyclists (non-motorist records)
- Total medical cost, and per capita
- Congestion + property damage cost, and per capita
- Total economic cost, and per capita
- QALYs cost: “Cost of life years lost (QALYs): ___, ___ per capita”
- Comprehensive cost, and per capita

### CDP level

Same fields as **County level**.

### Tract level

Same fields as **County level**.

---

## Individual crash

- Crash date and time
- Crash type
- Total occupant records (A) | Total non-motorist records (B) | Vehicle records (C), displayed as:  
  **Crash description:** [A+B] people directly affected by [C] vehicle collision ([A] vehicle occupants, [B] pedestrians or cyclists)
- Number of fatalities | Number of injuries
- Medical cost
- Congestion + property damage cost
- Total economic cost
- QALYs cost: “Cost of life years lost (QALYs)”
- Comprehensive cost

---

## Primary metric list

### Total

- Total comprehensive cost
- Crashes
- Fatalities
- Injuries
- Medical costs
- Congestion costs
- Property damage costs
- Total economic costs
- Cost of life years lost (QALYs)

### Per capita

- Total comprehensive costs
- Fatalities
- Injuries
- Medical costs
- Congestion costs
- Property damage costs
- Total economic costs
- Cost of life years lost (QALYs)
- Total comprehensive cost *(listed again in source spec)*

### Misc

- Cars per capita
- % of 0-car households

---

## Filters

- **Date** — Adjustable range (native date inputs); defaults to full span in data (`min_crash_date`–`max_crash_date`, e.g. 2024-01-01 through 2025-12-31 when both bounds are set in the UI).
- **Crash type**
- **Pedestrian or cyclist involved in crash** (checkbox)
