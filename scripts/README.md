# Cost calculation script

`calculate_device_costs.py` reads per-device power readings from the SQL Logger plugin, integrates Watts over time into kWh for the last hour and last 24 hours,
multiplies by your current Octopus tariff, and writes the results back to Indigo variables that the dashboard (or any other page) can chart.

## What it does

For each device listed in `DEVICES`:

1. Queries SQL Logger for the last hour and last 24 hours of power samples
2. Trapezoidal-integrates the samples to give energy used (kWh)
3. Multiplies by the current Octopus import tariff (pence/kWh) to get cost (£)
4. Writes four variables per device:
   - `kwh_<name>_hour` — kWh used in the last hour
   - `kwh_<name>_day` — kWh used in the last 24 hours
   - `cost_<name>_hour` — £ cost for the last hour
   - `cost_<name>_day` — £ cost for the last 24 hours
5. Writes two grand-total variables: `cost_total_hour` and `cost_total_day`

## Prerequisites

- **SQL Logger plugin** enabled and recording the power column for each device you want costed
- An Indigo **variable holding your current import tariff** in pence per kWh (e.g. `elec_unit_rate_p`) — updated by your Octopus integration of choice

## Install

1. Drop `calculate_device_costs.py` into `~/Library/Application Support/Perceptive Automation/Python Scripts/` (or wherever your Indigo Python Scripts folder lives)
2. Edit the `DEVICES` list at the top — set device IDs, short names and the SQL column that holds power readings for each
3. Edit `TARIFF_VAR_NAME` to match your tariff variable
4. In Indigo, create a Schedule (e.g. every 5 minutes) that runs this script

## Notes / caveats

- Trapezoidal integration is a reasonable approximation, not exact — gaps in SQL Logger samples will cause small under-counts. For a 5-minute sample interval the error is typically well under 1%.
- The SQL query (`device_history_<device_id>`) matches the SQL Logger plugin's default table naming. If you've customised the schema, adjust the SELECT.
- Variables are created if they don't exist. Variable names with prefixes like `cost_` and `kwh_` keep them grouped in the Indigo variables panel.
- If you're on a flat tariff this is overkill — but the same script handles Agile/Tracker where the per-period rate changes.

## Adapting for non-Octopus tariffs

The script reads `TARIFF_VAR_NAME` once per run, so if your supplier has different unit rates by time of day, just update that variable from another script
on the appropriate schedule (e.g. a Time of Use schedule). The cost calculation uses whatever rate is current when this script runs.

For true period-by-period tariff matching (e.g. Octopus Agile 30-minute slots), the integration loop would need to look up the tariff for each sample's timestamp.
Easy to extend — happy to share that version if anyone wants it.
