#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    IndigoSecrets_example.py
# Description: Optional template for the IndigoSecrets.py pattern.
#              See docs/secrets-pattern.md for full details.
#
# To USE this in your install:
#   1. Copy this file to:
#        /Library/Application Support/Perceptive Automation/IndigoSecrets.py
#      (note the rename — without the _example suffix)
#   2. Fill in the values you want to keep out of version control / out of
#      PluginConfig dialogs
#   3. Indigo plugins and scripts that follow the pattern will import from it
#      automatically; anything they don't find falls back to PluginConfig or a
#      default
#
# This file ships with placeholders only — it's safe to commit.
# The real IndigoSecrets.py is in every repo's .gitignore so it never gets pushed.

# ── Indigo server itself ─────────────────────────────────────────────────────
# If set, scripts that want to talk to Indigo's REST API can pick these up
# without prompting you. Optional — the dashboard HTML uses its own config.js
# or the browser localStorage form instead, so these are only needed for
# server-side scripts that hit the API.
INDIGO_URL     = ""   # e.g. "http://192.168.1.10:8176" or your Reflector URL
INDIGO_API_KEY = ""   # generate one in Indigo → Server Configuration → REST API

# ── Octopus Energy (optional, only if you build a direct fetcher) ────────────
# Not used by anything in this repo as shipped, but a sensible place to put
# them if you decide to extend the cost script with a direct Octopus API call
# rather than relying on an existing tariff plugin.
OCTOPUS_API_KEY      = ""   # from https://octopus.energy/dashboard/developer/
OCTOPUS_ACCOUNT      = ""   # e.g. "A-AAAA1111"
OCTOPUS_MPAN         = ""   # 13-digit electricity MPAN
OCTOPUS_ELEC_SERIAL  = ""   # electricity meter serial
OCTOPUS_GAS_MPRN     = ""   # 10-digit gas MPRN
OCTOPUS_GAS_SERIAL   = ""   # gas meter serial

# ── Notification routing (optional) ──────────────────────────────────────────
# If you have scripts that want to ping you when something interesting happens
# (battery low, optimiser unable to meet need, big cost spike), wiring the
# routing through here means you can change endpoint without touching every
# script.
PUSHOVER_USER_TOKEN = ""
NOTIFICATION_EMAIL  = ""

# ── Anything else ────────────────────────────────────────────────────────────
# Add your own keys as you go — webhook URLs, API tokens, anything you'd
# rather not paste into a PluginConfig field or hard-code into a script.
