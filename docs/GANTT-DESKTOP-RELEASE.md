# Gantt Desktop App Release

The desktop app is a thin packaged launcher around the local Gantt server.

## Local Source Run

```bash
python3 scripts/gantt_app.py
```

The launcher opens `http://127.0.0.1:8091/gantt.html` and stores runtime data outside the repository:

- macOS: `~/Library/Application Support/Plane Demand Hub Gantt`
- Windows: `%APPDATA%\\Plane Demand Hub Gantt`

## Local Package Build

Install PyInstaller, then build:

```bash
python3 -m pip install pyinstaller
pyinstaller packaging/plane-demand-hub-gantt.spec --noconfirm
```

The executable is written to `dist/PlaneDemandHubGantt` on macOS/Linux or `dist/PlaneDemandHubGantt.exe` on Windows.

## GitHub Release

GitHub Actions workflow: `.github/workflows/release-gantt-app.yml`

To publish a release:

```bash
git tag gantt-app-v0.1.0
git push origin gantt-app-v0.1.0
```

The workflow builds Windows and macOS zip assets and publishes them to the GitHub Release for that tag.

Manual workflow dispatch builds artifacts without publishing a release unless it runs from a `gantt-app-v*` tag.

Current release:

- `gantt-app-v0.1.0`
- `https://github.com/Kirrito-k423/DevTracking/releases/tag/gantt-app-v0.1.0`
- Assets: `PlaneDemandHubGantt-macos.zip`, `PlaneDemandHubGantt-windows.zip`
