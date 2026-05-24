# Optional: the `IndigoSecrets.py` pattern

This is the convention I use across all my plugins for keeping API keys, tokens, server URLs and other sensitive values out of plugin code, script files and PluginConfig dialogs. As far as I know nobody else in the Indigo community does it this way — it's just my own way of keeping things tidy. **It's entirely optional** — nothing in this repo requires it. If you'd rather configure things directly in scripts or PluginConfig, that works fine too.

If you fancy adopting the pattern (or are just curious how it works), this doc explains how the dashboard and cost-calc script fit in.

## The idea

- One file, `IndigoSecrets.py`, lives at a known canonical location
- Every script or plugin that needs a sensitive value imports from it with a per-key `try/except` so missing keys don't break anything
- Missing values fall back to PluginConfig (for plugins) or hard-coded defaults (for scripts)
- The file itself is **never committed** — it's in every repo's `.gitignore`. The `_example` version (shipped here) has empty placeholders and is safe to share

## Canonical location

```
/Library/Application Support/Perceptive Automation/IndigoSecrets.py
```

This directory exists for every Indigo install and survives version upgrades — no need to migrate when Indigo moves from 2025.1 to 2025.2 etc.

## Setup

1. Copy `IndigoSecrets_example.py` (in the root of this repo) to that location, renaming it to drop the `_example` suffix
2. Fill in whichever values you want to centralise
3. That's it — scripts that follow the pattern will pick them up automatically

## Canonical import pattern

This is the pattern I use in scripts that opt into it. It's safe to drop in even when the file doesn't exist — every key is wrapped in its own `try/except` so a missing single value doesn't blank the others:

```python
import sys as _sys
_sys.path.insert(0, "/Library/Application Support/Perceptive Automation")

try:
    from IndigoSecrets import INDIGO_API_KEY
except ImportError:
    INDIGO_API_KEY = ""   # falls back to empty; script handles the missing case

try:
    from IndigoSecrets import OCTOPUS_API_KEY
except ImportError:
    OCTOPUS_API_KEY = ""
```

## How the bits in this repo use it

### `pages/energy-showcase.html`

The HTML page itself doesn't read `IndigoSecrets.py` — it can't, it runs in your browser. It gets its credentials via `config.js` (when served by an Indigo plugin) or the browser connection form (when opened standalone).

But if you serve the page from your own plugin and want the credentials to come from `IndigoSecrets.py`, the pattern is straightforward — generate `config.js` at plugin startup from the imported values. Something like:

```python
# In your plugin's startup()
try:
    from IndigoSecrets import INDIGO_URL, INDIGO_API_KEY
except ImportError:
    INDIGO_URL = INDIGO_API_KEY = ""

# Then write config.js next to the HTML file
config_path = os.path.join(self.pages_dir, "config.js")
with open(config_path, "w") as f:
    f.write(f'window.INDIGO_CONFIG = {{"baseURL": "{INDIGO_URL}", "apiKey": "{INDIGO_API_KEY}"}};\n')
```

The Dashboards plugin does exactly this and generates its `config.js` from `IndigoSecrets.py` at startup.

### `scripts/calculate_device_costs.py`

As shipped, this script doesn't need any secrets — it reads the tariff from an existing Indigo variable. But if you extend it to fetch tariffs directly from Octopus, the API credentials are the obvious thing to wire through `IndigoSecrets.py`:

```python
import sys as _sys
_sys.path.insert(0, "/Library/Application Support/Perceptive Automation")

try:
    from IndigoSecrets import OCTOPUS_API_KEY, OCTOPUS_ACCOUNT
except ImportError:
    OCTOPUS_API_KEY = OCTOPUS_ACCOUNT = ""

if OCTOPUS_API_KEY and OCTOPUS_ACCOUNT:
    # fetch live tariff from Octopus directly
    ...
else:
    # fall back to reading the Indigo variable
    ...
```

## Why bother?

- **No secrets in PluginConfig dialogs.** PluginConfig values are stored unencrypted in Indigo's preferences plist — anyone with read access to that file (backup tools, sync clients, screen-share with a support tech) can see them.
- **No secrets in committed code.** The `_example` file is safe to share; the real one stays local.
- **Single source of truth.** Change an API key once, every plugin and script picks it up next run.
- **Survives Indigo upgrades.** The Application Support folder doesn't move between versions.

## Why you might not bother

- If you only have one or two plugins and they each have their own secrets, PluginConfig is simpler and works fine
- If you don't share your code publicly, hard-coding values is also fine — the trade-off is just convenience-vs-security
- The pattern is just my own way of doing things, not something the wider Indigo community uses — so if you fork the script and share it with someone else, they may need an explainer.

## See also

The full conventions I follow across all my plugins (Highsteads org) are described in the per-repo `CLAUDE.md` files of those plugins. The IndigoSecrets pattern is just one slice of that.
