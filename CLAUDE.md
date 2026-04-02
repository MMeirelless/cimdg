# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

CIM Data Generator (CIMDG) is a Splunk app (v1.0.0) — the first CIM-native synthetic data generator for Splunk. Users select CIM data models (Authentication, Network Traffic, Web, Endpoint, etc.) and generate synthetic events that are born CIM-compliant with correct fields, tags, and values — no Technology Add-on required. The app supports two generation modes: continuous streaming via modular inputs and on-demand batch generation via a custom search command (`| cimgenerate`). It uses Splunk's Simple XML for the configuration dashboard and Dashboard Studio for monitoring/validation dashboards. All Python code runs on Splunk's built-in Python 3 interpreter with stdlib only — no third-party dependencies.

## Development Setup

```bash
# Symlink the app into Splunk (one-time setup)
ln -s ~/dev/splunk-apps/cimdg $SPLUNK_HOME/etc/apps/cimdg

# After symlinking, file changes are live instantly in Splunk
# To reload without a full restart:
splunk reload apps
# Or via REST API (faster):
curl -k -u admin:password https://localhost:8089/services/apps/local/cimdg/_reload -X POST

# View the app at:
# http://localhost:8000/en-US/app/cimdg
```

## Validation & Testing

```bash
# AppInspect validation (required before release)
splunk-appinspect inspect ~/dev/splunk-apps/cimdg --mode precert

# AppInspect with output file for detailed review
splunk-appinspect inspect . --mode precert --output-file /tmp/appinspect_report.json

# XML syntax validation
find default/data/ui/views -name "*.xml" -exec xmllint --noout {} \;

# Python syntax check
python3 -m py_compile bin/cim_generator_modinput.py
python3 -m py_compile bin/cim_generator_command.py

# Unit tests
pytest tests/

# Clean install test (before releases)
mv local/ local.backup && splunk restart

# Verify app works with only default/ configs, then restore:
mv local.backup local/ && splunk restart
```

## Release Process

1. Update version in `default/app.conf`, `app.manifest`, and `CHANGELOG.md`
2. Update `CHANGELOG.md` (move Unreleased → Versioned section)
3. Commit and merge develop → prod (`cimdg-develop` → `cimdg-prod`)
4. Tag on the prod branch:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0" && git push origin v1.0.0
   ```

GitHub Actions automatically packages the `.spl` and creates a GitHub Release on tag push.

## Architecture

### Splunk App Structure

- `default/` — Committed default configs (app.conf, inputs.conf, props.conf, etc.). These ship with the app.
- `local/` — Developer/user-specific configs (views, inputs overrides). **Not in Git** — for development only.
- `appserver/static/` — JavaScript and CSS served by Splunk's web framework.
- `bin/` — Python modular input, custom search command, REST handlers, and generators.
- `bin/generators/` — One Python module per CIM data model (authentication.py, network_traffic.py, etc.).
- `bin/templates/` — JSON schema files defining fields, types, value pools, weights, and dependencies per CIM model.
- `lookups/` — CSV lookups for severity mappings, vendor products, etc.
- `metadata/` — App permissions (default.meta uses `sc_admin` for Cloud compatibility).
- `README/` — inputs.conf.spec for modular input parameter docs.
- `static/` — App icons (appIcon.png, appIcon_2x.png).

### Promotion Rules (local/ → default/)
Before committing, promote stable configs from `local/` to `default/`:
- **Safe to promote:** `data/ui/views/*.xml`, `data/ui/nav/default.xml`, `props.conf`, `transforms.conf`, `eventtypes.conf`, `tags.conf`, `collections.conf`, `savedsearches.conf`, `macros.conf`
- **Never promote:** `local.meta`, `app.conf`, `authentication.conf`, `passwords.conf`, `server.conf`, `inputs.conf` (user-specific input stanzas)

If you find any files other than those on the safe list that could be promoted, including those listed in the "Never promote" list, please identify them so the user can determine whether there are exceptions.

### Key Files

| File | Purpose |
|------|---------|
| `bin/cim_generator_modinput.py` | Modular input for continuous streaming (inherits `splunklib.modularinput.Script`) |
| `bin/cim_generator_command.py` | Custom generating search command (`| cimgenerate model=X count=N`) |
| `bin/cim_generator_rest_handler.py` | REST handler for dashboard integration (start/stop, batch trigger) |
| `bin/generators/base.py` | Base generator: entity pools, field generation, cross-model correlation |
| `bin/generators/authentication.py` | Authentication data model generator |
| `bin/generators/network_traffic.py` | Network Traffic data model generator |
| `bin/generators/web.py` | Web data model generator |
| `bin/generators/endpoint.py` | Endpoint data model generator (Processes, Filesystem, Registry, Services, Ports) |
| `bin/templates/*.json` | JSON schemas per CIM model (fields, values, weights, dependencies) |
| `default/inputs.conf` | Modular input stanzas (all disabled=1 by default) |
| `default/props.conf` | Sourcetype definitions with `KV_MODE = json` for CIM field extraction |
| `default/eventtypes.conf` | Event types matching each `synthetic:*` sourcetype |
| `default/tags.conf` | CIM tags applied to event types |
| `default/commands.conf` | Custom search command registration (`cimgenerate`) |
| `default/restmap.conf` | REST endpoint registration for dashboard integration |
| `default/data/ui/views/generator_config.xml` | Generator Configuration dashboard (SimpleXML form) |
| `default/data/ui/views/generation_status.xml` | Generation Status & Volume Monitor (Dashboard Studio) |
| `default/data/ui/views/cim_validation.xml` | CIM Validation dashboard (Dashboard Studio) |

### How It Works

1. **Continuous mode**: Modular input (`cim_generator_modinput.py`) streams events at configured intervals. Each stanza specifies data model, EPS, target index, and optional value overrides.
2. **Batch mode**: Custom search command (`| cimgenerate model="Authentication" count=10000 timerange="-24h"`) generates on-demand, pipeable to `| collect`.
3. **Generation pipeline**: `GeneratorFactory` → model-specific generator → `BaseGenerator.generate()` → JSON event with CIM-native fields → `EventWriter` or search results.
4. **CIM compliance chain**: `props.conf` (KV_MODE=json) → `eventtypes.conf` (sourcetype match) → `tags.conf` (CIM tags) → data model constraint captures events.
5. **Cross-model correlation**: Session correlation engine shares `session_id`, `user`, `src` values across Authentication → Network Traffic → Web events.
6. **Dashboard integration**: REST handler bridges UI controls to input management (start/stop/adjust) and batch triggers.

### Splunk-Specific Patterns

- **Modular inputs** over scripted inputs — required for Cloud compatibility (native UI config, auto-REST, credential management)
- **Sourcetype convention**: `synthetic:<model_name>` (e.g., `synthetic:authentication`, `synthetic:network_traffic`)
- **Dedicated index**: `synthetic_cim` with 7-day retention (Enterprise only; document manual creation for Cloud)
- **Events are born CIM-compliant**: JSON payload uses CIM field names directly (action, user, src, dest) — minimal aliasing needed
- **Python stdlib only**: No third-party libraries — `random`, `ipaddress`, `datetime`, `json`, `string`, `os`
- **All inputs ship disabled**: `disabled = 1` in every `default/inputs.conf` stanza
- **Rate limiting**: Hard ceiling of 1000 EPS configurable in the generator
- Views use **Require.js AMD** module loading — Splunk's bundled version
- The `local/` directory is excluded from Git and AppInspect packaging

### Cloud Compatibility

- No `indexes.conf` in Cloud-targeted packages (document manual index creation)
- No `limits.conf`
- `sc_admin` in all metadata references (never `admin`)
- `python.version = python3` in `commands.conf`, `inputs.conf`, `restmap.conf`
- All files 644, directories 755
- `enableSched = 0` for scheduled searches by default
- Package under 128MB

### CIM Data Models Supported

**MVP (v0.1)**: Authentication, Network Traffic, Web, Endpoint (Processes), Malware, Intrusion Detection, DNS

**v1.0**: + Vulnerabilities, Change, Email, Network Sessions, Alerts, DLP, Certificates, Endpoint (Filesystem, Registry, Services, Ports), Updates

**v1.5**: + Performance, JVM, Databases, Inventory, Ticket Management, Interprocess Messaging, Splunk Audit Logs

## Branching & Commits

- `cimdg-prod` — Production releases
- `cimdg-develop` — Daily integration
- `feature/*`, `bugfix/*` — Branch from `cimdg-develop`; `hotfix/*` — Branch from `cimdg-prod`

### Cross-Branch File Sync

Shared infrastructure files must be kept in sync across both branches (`cimdg-develop`, `cimdg-prod`). When any of these files are modified, cherry-pick or copy the changes to the other branch:

- `.github/workflows/` — CI/CD workflows
- `CLAUDE.md` — Development guidelines
- `.claude/` — Skills, commands, settings

### Release Tags

| Tag pattern | Example | Triggers |
|------------|---------|----------|
| `v*.*.*` | `v1.0.0` | Release workflow → `cimdg-1.0.0.spl` |

Versions in `app.conf` and `app.manifest` must be numeric-only (`1.0.0`) — Splunkbase requires strict `Major.Minor.Revision` format.

Commit format (Conventional Commits):
```
feat(generator): Add Network Traffic data model support
fix(modinput): Resolve event timestamp precision issue
feat(dashboard): Add CIM validation panel
docs: Update installation instructions
```

## Debugging

```bash
# Tail Splunk logs filtered to this app
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i cim_generator

# Check modular input logs
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i "cim_synthetic"

# JS errors appear in browser DevTools console (F12)
```

**App not showing / changes not appearing:** Check symlink (`ls -la $SPLUNK_HOME/etc/apps/ | grep cimdg`), run `splunk reload apps`, and hard-refresh the browser (Ctrl+Shift+R).

**AppInspect failures:** Common causes are missing `app.manifest` fields, hardcoded credentials, `eval()` usage in JS, or missing `python.version = python3`.

**Generated data not appearing in CIM model:** Check the chain: `props.conf` (sourcetype defined?) → `eventtypes.conf` (eventtype matches sourcetype?) → `tags.conf` (CIM tags applied?) → verify with `| datamodel <Model> search | head 10`.
