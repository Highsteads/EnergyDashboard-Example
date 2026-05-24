#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    calculate_device_costs.py
# Description: Read per-device power from SQL Logger, integrate to kWh per hour/day,
#              multiply by Octopus tariff, write results back to Indigo variables.
# Author:      Highsteads / CliveS (open source — adapt freely)
# Date:        24-05-2026
# Version:     1.0
#
# This is an EXAMPLE script — the device IDs, variable names and tariff variable
# name will need adapting for your own Indigo install. The structure / pattern is
# the bit worth copying.
#
# Run from an Indigo Schedule (hourly is sensible) or trigger.
# Requires: SQL Logger plugin enabled and recording the powerW state for each
#           device you want to cost.

from datetime import datetime, timedelta

# ═════════════════════════════════════════════════════════════════════════════
# 🔐  OPTIONAL: IndigoSecrets.py pattern
# ═════════════════════════════════════════════════════════════════════════════
# This script doesn't need any secrets as shipped — it reads the tariff from
# an existing Indigo variable. But if you want to extend it to fetch tariff
# data directly from Octopus (instead of via a plugin), the canonical place
# to put your Octopus API credentials is /Library/Application Support/Perceptive
# Automation/IndigoSecrets.py — see docs/secrets-pattern.md for the full setup.
#
# The import below is harmless if you don't use the pattern (missing values
# just fall back to empty strings). Delete this block if you'd rather not
# have it at all.
# ─────────────────────────────────────────────────────────────────────────────
import sys as _sys
_sys.path.insert(0, "/Library/Application Support/Perceptive Automation")
try:
    from IndigoSecrets import OCTOPUS_API_KEY
except ImportError:
    OCTOPUS_API_KEY = ""
try:
    from IndigoSecrets import OCTOPUS_ACCOUNT
except ImportError:
    OCTOPUS_ACCOUNT = ""
# (Per-key try/except — a missing single key must NOT blank the others.)

# ═════════════════════════════════════════════════════════════════════════════
# ⚙️  CONFIG — EDIT FOR YOUR SETUP
# ═════════════════════════════════════════════════════════════════════════════

# Device IDs to calculate costs for. Each entry:
#   (indigo_device_id, "short_name_for_variable", "state_column_in_sql")
#
# IMPORTANT: every plugin uses a different state name for "instantaneous power
# in Watts". You will need to look at YOUR device in Indigo (right-click →
# Show Custom States) and find the right one. Some common ones:
#   - "curEnergyLevel"  — many Shelly plugins, generic Z-Wave power-monitoring
#   - "powerW"          — some custom plugins
#   - "power"           — Shelly Gen2/3 native API, some Tasmota devices
#   - "apparentPower"   — some energy monitors
#   - "instantPower"    — others again
# Whatever it is, that state must be a NUMBER in Watts, and SQL Logger must be
# configured to log it.
#
# The examples below are placeholders — replace with your own device IDs and
# the state column that holds power for each device.
DEVICES = [
    (123456789,  "tv",              "curEnergyLevel"),
    (234567890,  "tumble_dryer",    "curEnergyLevel"),
    (345678901,  "washing_machine", "curEnergyLevel"),
    (456789012,  "nas",             "curEnergyLevel"),
    # … add your own
]

# Indigo variable name that holds the current Octopus import rate in pence/kWh.
# Updated by your Octopus integration (e.g. the TariffAnalyser plugin or a script).
TARIFF_VAR_NAME = "elec_unit_rate_p"

# Variable prefix for the written-back results.
# Output variables will be e.g.  cost_samsung_tv_hour, cost_samsung_tv_day,
#                                kwh_samsung_tv_hour,  kwh_samsung_tv_day
OUTPUT_PREFIX_COST = "cost_"
OUTPUT_PREFIX_KWH  = "kwh_"

# ═════════════════════════════════════════════════════════════════════════════
# END CONFIG
# ═════════════════════════════════════════════════════════════════════════════


def log(message, level="INFO"):
    """Millisecond-precision logger (matches the CliveS plugin convention)."""
    ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    indigo.server.log(f"[{ts}] {message}", level=level)


def get_tariff_p_per_kwh():
    """Read current import tariff from an Indigo variable (string → float)."""
    try:
        return float(indigo.variables[TARIFF_VAR_NAME].value)
    except (KeyError, ValueError) as e:
        log(f"Could not read tariff variable {TARIFF_VAR_NAME!r}: {e}", level="ERROR")
        return None


def integrate_kwh_from_sql(device_id, column, hours_back):
    """
    Pull power-W samples from SQL Logger for the last N hours, integrate to kWh.

    Uses trapezoidal integration: kWh = sum( ((p1 + p2) / 2) * (t2 - t1) / 3600 ) / 1000
    Returns kWh as a float, or None if no data.

    Requires the SQL Logger plugin to be enabled and logging this device's column.
    """
    sql_plugin = indigo.server.getPlugin("com.perceptiveautomation.indigoplugin.sql-logger")
    if not (sql_plugin and sql_plugin.isEnabled()):
        log("SQL Logger plugin not enabled — cannot integrate kWh", level="ERROR")
        return None

    # SQL Logger schema varies a bit — adjust this query for your setup.
    # The default table is `device_history_<device_id>` with timestamp + columns.
    cutoff = (datetime.now() - timedelta(hours=hours_back)).strftime("%Y-%m-%d %H:%M:%S")
    sql = (
        f"SELECT ts, {column} FROM device_history_{device_id} "
        f"WHERE ts >= '{cutoff}' AND {column} IS NOT NULL ORDER BY ts ASC"
    )
    try:
        reply = sql_plugin.executeAction("executeSqlSelect", props={"sql": sql})
        rows = reply.get("rows", []) if isinstance(reply, dict) else []
    except Exception as e:
        log(f"SQL query failed for device {device_id}: {e}", level="ERROR")
        return None

    if len(rows) < 2:
        return 0.0  # not enough samples

    # Trapezoidal integration
    total_kwh = 0.0
    for (t1, p1), (t2, p2) in zip(rows[:-1], rows[1:]):
        if not isinstance(t1, datetime):
            t1 = datetime.fromisoformat(str(t1))
            t2 = datetime.fromisoformat(str(t2))
        dt_hours = (t2 - t1).total_seconds() / 3600.0
        if dt_hours <= 0 or dt_hours > 1:
            continue  # skip gaps longer than 1 hour
        avg_w = (float(p1) + float(p2)) / 2.0
        total_kwh += avg_w * dt_hours / 1000.0
    return round(total_kwh, 3)


def write_variable(name, value):
    """Create the variable if it doesn't exist, then update it. Values are stored as strings."""
    if name not in indigo.variables:
        indigo.variable.create(name, str(value))
    else:
        indigo.variable.updateValue(name, str(value))


def main():
    log("Calculating per-device costs…")

    tariff = get_tariff_p_per_kwh()
    if tariff is None:
        log("Aborting — no tariff available", level="ERROR")
        return

    log(f"Current import tariff: {tariff:.2f}p / kWh")

    total_hour_cost = 0.0
    total_day_cost = 0.0

    for device_id, short_name, column in DEVICES:
        if device_id not in indigo.devices:
            log(f"Device {device_id} ({short_name}) not found — skipping", level="WARNING")
            continue

        kwh_hour = integrate_kwh_from_sql(device_id, column, hours_back=1)
        kwh_day  = integrate_kwh_from_sql(device_id, column, hours_back=24)

        if kwh_hour is None or kwh_day is None:
            log(f"No SQL data for {short_name} ({device_id})", level="WARNING")
            continue

        cost_hour = round(kwh_hour * tariff / 100.0, 4)  # → £
        cost_day  = round(kwh_day  * tariff / 100.0, 4)

        write_variable(f"{OUTPUT_PREFIX_KWH}{short_name}_hour",  kwh_hour)
        write_variable(f"{OUTPUT_PREFIX_KWH}{short_name}_day",   kwh_day)
        write_variable(f"{OUTPUT_PREFIX_COST}{short_name}_hour", cost_hour)
        write_variable(f"{OUTPUT_PREFIX_COST}{short_name}_day",  cost_day)

        log(f"  {short_name:20s}  {kwh_hour:5.3f} kWh/h  £{cost_hour:.4f}  "
            f"|  {kwh_day:5.2f} kWh/24h  £{cost_day:.3f}")

        total_hour_cost += cost_hour
        total_day_cost += cost_day

    write_variable(f"{OUTPUT_PREFIX_COST}total_hour", round(total_hour_cost, 4))
    write_variable(f"{OUTPUT_PREFIX_COST}total_day",  round(total_day_cost,  3))

    log(f"Totals: £{total_hour_cost:.4f}/hour, £{total_day_cost:.3f}/day "
        f"across {len(DEVICES)} devices")


if __name__ == "__main__":
    main()
