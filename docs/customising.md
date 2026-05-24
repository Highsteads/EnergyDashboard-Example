# Adapting the dashboard for your setup

The whole dashboard is wired through a single `ID` config block near the top of `pages/energy-showcase.html`. Edit that block to point at your own
Indigo device IDs and everything else follows.

## Finding device IDs

In the Indigo client:
- **Right-click a device → Copy Internal ID** — pastes the numeric ID
- Or in the **Scripting Shell**: `print(indigo.devices["Living Room Lamp"].id)`

## The config block

Look for this block in `energy-showcase.html`:

```javascript
const ID = {
    BATTERY_MANAGER: 93061288,    // Battery Manager device
    SIGEN_INVERTER:  1563154425,  // Sigenergy Inverter
    ZONES: [
        [1886011292, "Bathroom"],
        ...
    ],
    ECOFLOW: [
        [1786840251, "Bathroom River 3+"],
        ...
    ],
};
const BATTERY_CAPACITY_KWH = 35.04;
```

## What each section needs

### Energy section (hero KPIs, flow diagram, SOC gauge, today's totals)

Needs a Sigenergy inverter via the [SigenEnergyManager plugin](https://github.com/Highsteads/SigenEnergyManager) — it exposes:
- `pvPowerWatts`, `pvDailyKwh`
- `batterySoc`, `batteryPowerWatts`, `batteryDailyChargeKwh`, `batteryDailyDischargeKwh`
- `gridPowerWatts`, `gridDailyImportKwh`, `gridDailyExportKwh`
- `homePowerWatts`, `homeDailyKwh`

If you have a different inverter, you'll need to either:
- Adapt the field names in the `render()` function to match your inverter's state names, or
- Write a small Python script that reads your inverter and writes equivalent state names to a custom Indigo device

### Tariffs section

Needs Indigo variables containing live Octopus tariff data:
- `gas_today_kwh`, `gas_month_kwh`, `gas_yesterday_kwh`, `gas_unit_rate_p`
- `export_rate_p`, `export_month_kwh`, `export_month_revenue_gbp`, `export_yesterday_kwh`
- `elec_unit_rate_p`
- `sigen_today_pv_kwh`, `sigen_today_home_kwh`, `sigen_today_import_kwh`

Most Octopus integrations expose these. The dashboard reads them by name, so the variable names need to match (or you change the names in the JS to match yours).

### Heating section

Needs RAMSES ESP TRVs (or any thermostat device with `temperatureInput1`, `setpointHeat` and a `valve-position` state). For other thermostat types, adjust the field names in `zoneData = ID.ZONES.map(...)`.

The +/− buttons call `indigo.thermostat.setHeatSetpoint` which is the standard Indigo thermostat command, so they should work with any thermostat that
supports a heat setpoint.

### EcoFlow section

Needs the [EcoFlow Cloud plugin](https://github.com/Highsteads/EcoFlowCloud). The dashboard reads `batteryLevel` from each device's states.

### Sections that don't need configuring

- Security overview — auto-discovers contact sensors and motion sensors by name pattern
- Device inventory — counts all devices in the system
- System health — uses whichever Mac the Indigo server is running on

## What to do if you don't have something

The dashboard degrades gracefully — sections will just show `0` or empty rather than break. Feel free to comment out entire sections from the layout
HTML if you'd rather hide them.

## Optional: `IndigoSecrets.py`

If you already use the `IndigoSecrets.py` pattern (a single file at `/Library/Application Support/Perceptive Automation/IndigoSecrets.py` that holds
API keys and other sensitive values), the cost-calc script in this repo opts into it automatically — it tries to import `OCTOPUS_API_KEY` and
`OCTOPUS_ACCOUNT` with a per-key `try/except` so missing values are harmless.

If you don't use the pattern, ignore this — everything works without it. See [secrets-pattern.md](secrets-pattern.md) for the full setup if you fancy
adopting it.

## Adding your own sections

The pattern is consistent:
1. Add a `<div class="card s4"><h3>Your Section</h3><div id="yourId"></div></div>` to the `buildLayout()` function
2. Read the data you need from `byId[deviceId]` or `varByName[varName]` inside `render()`
3. Either populate `innerHTML` directly or call `makeChart("yourId", "bar", data, options)` for a chart

Ask Claude to add the section for you — describe what you want shown and from which device, and it'll fit it in with the existing styling.
