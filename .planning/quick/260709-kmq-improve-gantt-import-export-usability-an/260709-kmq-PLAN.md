---
status: ready
created: 2026-07-09
quick_id: 260709-kmq
---

# Quick Task 260709-kmq: Improve Gantt Import/Export Usability And Desktop Release Packaging

## Scope

- Replace the migration snapshot-only affordance with clear import/export controls.
- Export a zip migration package from the browser/server.
- Import a zip migration package through a button or drag/drop.
- Keep report generation available but not presented as a second migration export.
- Add a desktop app launcher suitable for PyInstaller packaging.
- Add GitHub Actions release workflow for Windows and macOS installers/executables.

## Plan

1. Extend the local server with portable zip download/import endpoints.
2. Update generated Gantt HTML controls and drag/drop import behavior.
3. Add desktop launcher plus PyInstaller spec.
4. Add GitHub Release workflow for cross-platform builds.
5. Regenerate delivery and portable snapshots.
6. Verify Python compile, server endpoints, zip import/export, and generated page markers.

## Verification

- Python compile passes.
- Export zip endpoint returns a valid package containing `gantt-local-edits.json`.
- Import zip endpoint validates and restores a snapshot.
- Rebuilt Gantt page contains import/export controls and drag/drop handlers.
- Portable snapshot remains at the recovered 49 task / 46 event state.
