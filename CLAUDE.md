# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

DASH is a Splunk app (v1.0.0) — a visual style builder for Splunk classic XML dashboards. Users design app-wide CSS themes through a form-based interface, preview them across use case templates (Cybersecurity, IT Ops, APM — 5 dashboards each), and export styled Splunk apps. It uses Splunk's Simple XML dashboard framework with custom JavaScript/jQuery frontend and Splunk KV Store for template persistence. There is no Node.js build step — all JS/CSS is served as-is by Splunk's web server.

## Development Setup

```bash
# Symlink the app into Splunk (one-time setup)
ln -s ~/dev/splunk-apps/dash $SPLUNK_HOME/etc/apps/dash

# After symlinking, file changes are live instantly in Splunk
# To reload without a full restart:
splunk reload apps
# Or via REST API (faster):
curl -k -u admin:password https://localhost:8089/services/apps/local/dash/_reload -X POST

# View the app at:
# http://localhost:8000/en-US/app/dash
```

## Validation & Testing

```bash
# AppInspect validation (required before release)
splunk-appinspect inspect ~/dev/splunk-apps/dash --mode precert

# AppInspect with output file for detailed review
splunk-appinspect inspect . --mode precert --output-file /tmp/report.json

# XML syntax validation
xmllint --noout local/data/ui/views/builder.xml

# Unit tests (currently empty, future use)
pytest tests/

# Clean install test (before releases)
mv local/ local.backup && splunk restart

# Verify app works with only default/ configs, then restore:
mv local.backup local/ && splunk restart
```

## Release Process

1. Update version in `default/app.conf`, `app.manifest`, and `CHANGELOG.md`
2. Update `CHANGELOG.md` (move Unreleased → Versioned section)
3. Commit and merge develop → prod (`dash-develop` → `dash-prod` or `lite-develop` → `lite-prod`)
4. Tag on the prod branch:
   - Full DASH: `git tag -a v1.1.0 -m "Release version 1.1.0" && git push origin v1.1.0`
   - DASH Lite: `git tag -a lite-v1.0.0 -m "Release DASH Lite version 1.0.0" && git push origin lite-v1.0.0`

GitHub Actions automatically packages the `.spl` and creates a GitHub Release on tag push. The workflow validates that the tag variant matches the `[package] id` in `app.conf` — tagging the wrong branch will fail early.

## Architecture

### Splunk App Structure

- `default/` — Committed default configs (app.conf, navigation). These ship with the app.
- `local/` — Developer/user-specific configs (views, collections.conf, transforms.conf). **Not in Git** — these are the actual view files during development.
- `appserver/static/` — JavaScript and CSS served by Splunk's web framework.
- `lookups/` — Sample CSV data (legacy, used by gallery view).
- `bin/` — Python REST handlers and use case dashboard definitions.

### Promotion Rules (local/ → default/)
Before committing, promote stable configs from `local/` to `default/`:
- **Safe to promote:** `data/ui/views/*.xml`, `data/ui/nav/default.xml`, `collections.conf`, `transforms.conf`
- **Never promote:** `local.meta`, `app.conf`, `authentication.conf`, `passwords.conf`, `server.conf`

If you find any files other than those on the safe list that could be promoted, including those listed in the "Never promote" list, please identify them so the user can determine whether there are exceptions.

### Key Files

| File | Purpose |
|------|---------|
| `default/data/ui/views/builder.xml` | Main builder dashboard (Simple XML) |
| `appserver/static/js/builder.js` | Builder logic — dynamic preview engine, carousel, style manager |
| `appserver/static/js/use_cases.js` | AMD module: 15 dashboard definitions (3 use cases × 5 dashboards) |
| `appserver/static/css/preview.css` | CSS variables for the live preview panel |
| `appserver/static/css/builder.css` | Styling for the builder UI chrome and carousel |
| `bin/create_app_handler.py` | REST handler for generating styled Splunk apps from the Builder |
| `bin/gallery_handler.py` | REST handler for Gallery — save, delete (single + bulk), clone, and create apps from gallery items |
| `bin/app_builder.py` | Shared app-building logic (used by both create_app and gallery handlers) |
| `bin/use_case_dashboards.py` | Python mirror of use_cases.js for Simple XML generation |
| `default/data/ui/views/gallery.xml` | Gallery dashboard (Simple XML) |
| `appserver/static/js/gallery.js` | Gallery logic — card rendering, create/customize/delete/bulk-delete actions |
| `appserver/static/css/gallery.css` | Styling for the gallery card grid and mini-previews |
| `default/collections.conf` | KV Store collection definition (`gallery_items`) |
| `default/transforms.conf` | Maps `gallery_items` lookup to KV Store |

### How It Works

1. `builder.xml` is a Splunk Simple XML dashboard that loads `builder.js` and `use_cases.js` via Require.js
2. Users select a use case (Cybersecurity, IT Ops, APM) and navigate 5 dashboards via a carousel
3. `builder.js` dynamically creates `SearchManager` + `ChartView`/`TableView`/`SingleView` instances from `use_cases.js` definitions — all searches use `makeresults` (no CSV dependencies)
4. The Style Manager form collects CSS variable values (colors, fonts, logos) and applies them to the live preview via `preview.css`
5. "Create Styled App" sends the style config + selected use case to `create_app_handler.py`, which generates 5 Simple XML dashboards using `use_case_dashboards.py`
6. "Save to Gallery" sends the style config + images to `gallery_handler.py`, which stores them in the `gallery_items` KV Store collection and saves images to disk
7. The Gallery page (`gallery.js`) loads items from KV Store and MB2 inspirations from `inspirations.json`, letting users create apps, customize styles, or delete items
8. Backbone.js `ModalView` (in `appserver/static/lib/modal-view.js`) powers the Gallery actions and app creation dialogs

### Splunk-Specific Patterns

- Views use **Require.js AMD** module loading — Splunk's bundled version, not a standalone install
- Search results flow through **SearchManager → ResultsModel → View** (Splunk MVC pattern)
- The `local/` directory is excluded from Git and AppInspect packaging — configs there are for development only; views intended for distribution must eventually be moved to `default/`
- KV Store access uses `splunkjs` SDK calls, not direct REST

## Branching & Commits

- `dash-prod` — DASH full version production releases
- `dash-develop` — DASH full version daily integration
- `lite-prod` — DASH Lite production releases
- `lite-develop` — DASH Lite daily integration
- `feature/*`, `bugfix/*` — Branch from the relevant develop branch; `hotfix/*` — Branch from the relevant prod branch

### Cross-Branch File Sync

Shared infrastructure files must be kept in sync across all four branches (`dash-develop`, `dash-prod`, `lite-develop`, `lite-prod`). When any of these files are modified, cherry-pick or copy the changes to all other branches:

- `.github/workflows/` — CI/CD workflows (unified for both variants)
- `CLAUDE.md` — Development guidelines
- `.claude/` — Skills, commands, settings

App-specific files (views, JS, CSS, Python handlers, configs) stay branch-specific — they differ between full DASH and DASH Lite.

### Release Tags

| Variant | Tag pattern | Example | Triggers |
|---------|------------|---------|----------|
| Full DASH | `v*.*.*` | `v1.1.0` | Release workflow → `dash-1.1.0.spl` |
| DASH Lite | `lite-v*.*.*` | `lite-v1.0.0` | Release workflow → `dash_lite-1.0.0.spl` |

Versions in `app.conf` and `app.manifest` must be numeric-only (`1.0.0`, not `1.0.0-lite`) — Splunkbase requires strict `Major.Minor.Revision` format.

Commit format (Conventional Commits):
```
feat(builder): Add drag-and-drop panel reordering
fix(gallery): Resolve dashboard preview loading issue
docs: Update installation instructions
```

## Debugging

```bash
# Tail Splunk logs filtered to this app
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i dash

# JS errors appear in browser DevTools console (F12)
```

**App not showing / changes not appearing:** Check symlink (`ls -la $SPLUNK_HOME/etc/apps/ | grep dash`), run `splunk reload apps`, and hard-refresh the browser (Ctrl+Shift+R).

**AppInspect failures:** Common causes are missing `app.manifest` fields, hardcoded credentials, or `eval()` usage in JS.
