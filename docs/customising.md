# Adapting the dashboard for your setup

The dashboard is configured via a single `CONFIG` block near the top of `pages/energy-showcase.html`. Every section is **role-based** — you map your own
devices to roles like "the device that publishes solar power" rather than naming specific plugins. This means the page works with any inverter, any
thermostat, any battery monitor — not just the ones I happen to use.

## Finding device IDs

In the Indigo client, right-click a device → **Copy ID** — pastes the numeric ID ready to drop into the config block.

## The config block

There are five top-level config objects, all near the top of the file:

```javascript
const ENERGY            = { deviceId: null, states: {...}, battery_capacity_kwh: 10 };
const OPTIMISER         = { deviceId: null, states: {...} };
const HEATING           = { auto_discover: true, devices: null };
const BACKUP_BATTERIES  = { auto_discover: true, devices: null };
const VARIABLES         = {...};
const POLL_INTERVAL_MS  = 5000;
```

Every section will hide gracefully or show "no data configured" if you leave it unconfigured — you don't have to use all of them.

## ENERGY — the solar / battery / grid / home section

This is the main event. Set `deviceId` to the Indigo device that publishes power and energy readings, then fill in the `states` map so each role points at
the matching state name on your device.

### Finding your device's state names

There is no Indigo-wide standard for energy device state names — every plugin invents its own. To find yours:

1. In the Indigo client, **right-click your inverter / energy monitor device → Show Custom States**
2. A panel opens listing every state the device publishes and its current value
3. Identify which state holds each role (solar power in Watts, battery SOC, grid flow, home consumption, etc.) and copy its exact name into the `states` map

For example, if your device exposes a `currentPowerW` state for the live solar output, you'd set:

```javascript
solar_power_w: "currentPowerW",
```

### Minimum useful configuration

The hero KPIs, flow diagram and SOC gauge need these nine roles mapped:

```javascript
const ENERGY = {
    deviceId: 123456789,             // ← your inverter / energy device ID
    states: {
        solar_power_w:    "...",     // instantaneous solar W
        solar_kwh:        "...",     // today's solar kWh
        battery_soc:      "...",     // battery SOC 0-100
        battery_power_w:  "...",     // +ve charging, -ve discharging
        grid_power_w:     "...",     // +ve importing, -ve exporting
        grid_import_kwh:  "...",     // today's grid import kWh
        grid_export_kwh:  "...",     // today's grid export kWh
        home_power_w:     "...",     // instantaneous home W
        home_kwh:         "...",     // today's home kWh
    },
    battery_capacity_kwh: 10,        // your battery's usable capacity
};
```

### If you don't have a battery

Leave the `battery_*` roles as empty strings — the SOC gauge will show 0% and the battery health card will be empty, but everything else still works. The
flow diagram pipes for the battery just won't animate.

### If you don't have solar at all

Set `deviceId: null` to hide the entire energy section. The dashboard is still useful for tariffs, gas, heating, security and device inventory.

### Sign conventions

The dashboard expects:

- `battery_power_w`: positive when **charging**, negative when **discharging**
- `grid_power_w`: positive when **importing**, negative when **exporting**

If your device uses the opposite convention, multiply by -1 in a custom device wrapper or change the comparison logic in the render function.

## OPTIMISER — optional decision-making device

Some battery management plugins publish a "current action" string and reasoning text (e.g. "Solar Overflow Export — battery 27.5 kWh, 9.6h to dusk"). If
yours does, point `OPTIMISER.deviceId` at it and the dashboard will surface that text live. If not, leave it as `null` and the section will show a friendly
"no optimiser configured" message.

The state name map works exactly like ENERGY — match the role keys to whatever your device uses.

## HEATING — auto-discovers any thermostat

By default, the heating section auto-discovers every device whose class contains `"Thermostat"` — that's the standard Indigo thermostat class, which
just about every thermostat plugin uses.

The +/− buttons call `indigo.thermostat.setHeatSetpoint`, which is the standard Indigo thermostat command — works with anything that follows the
standard class.

If you'd rather pick specific zones manually instead of auto-discovering all of them:

```javascript
const HEATING = {
    auto_discover: false,
    devices: [
        [1886011292, "Bathroom"],
        [545736860,  "Bedroom"],
        // …
    ],
};
```

If you don't have any thermostats, the heating section will just show empty.

## BACKUP_BATTERIES — auto-discovers any battery device

Auto-discovers any device with a numeric `batteryLevel` (or `soc` / `batterySoc`) state. That covers UPS devices, portable power stations, plugins that
expose battery telemetry, and anything custom you've wired up.

Manual override works the same as heating:

```javascript
const BACKUP_BATTERIES = {
    auto_discover: false,
    devices: [
        [111222333, "Garage UPS"],
        [444555666, "Office Power Station"],
    ],
};
```

## VARIABLES — tariff and gas data

Indigo variable names that hold your tariff and gas data. All optional — missing variables show as zero.

```javascript
const VARIABLES = {
    gas_today_kwh:        "gas_today_kwh",
    gas_yesterday_kwh:    "gas_yesterday_kwh",
    gas_month_kwh:        "gas_month_kwh",
    gas_unit_rate_p:      "gas_unit_rate_p",
    elec_unit_rate_p:     "elec_unit_rate_p",
    export_rate_p:        "export_rate_p",
    export_month_kwh:     "export_month_kwh",
    export_month_revenue: "export_month_revenue_gbp",
    export_yesterday_kwh: "export_yesterday_kwh",
    yesterday_pv_kwh:     "yesterday_pv_kwh",
    yesterday_home_kwh:   "yesterday_home_kwh",
    yesterday_import_kwh: "yesterday_import_kwh",
    optimiser_plan:       "battery_optimiser_status",
};
```

The right-hand side is the actual Indigo variable name — change it to match whatever your tariff integration writes. Most Octopus integrations expose
something similar.

If you don't have tariff data, the tariff section will show zeros. That's fine — the rest of the dashboard works regardless.

## Sections that don't need configuring

- **Security overview** — auto-discovers contact sensors and motion sensors by name pattern
- **Device inventory** — counts all devices in the system
- **System health** — total device count and healthy/errored split

## Optional: `IndigoSecrets.py`

I keep my own API keys and other sensitive values in a single file at `/Library/Application Support/Perceptive Automation/IndigoSecrets.py`. It is
just my own convention — as far as I know nobody else does it this way — but the cost-calc script opts into it automatically if the file exists,
importing `OCTOPUS_API_KEY` and `OCTOPUS_ACCOUNT` with a per-key `try/except` so missing values are harmless.

If you don't use the pattern, ignore this — everything works without it. See [secrets-pattern.md](secrets-pattern.md) for the full setup if you fancy
adopting it.

## Adding your own sections

The pattern is consistent:
1. Add a `<div class="card s4"><h3>Your Section</h3><div id="yourId"></div></div>` to the `buildLayout()` function
2. Read the data you need from `byId[deviceId]` or `varByName[varName]` inside `render()`
3. Either populate `innerHTML` directly or call `makeChart("yourId", "bar", data, options)` for a chart

Ask Claude to add the section for you — describe what you want shown and from which device, and it'll fit it in with the existing styling.
