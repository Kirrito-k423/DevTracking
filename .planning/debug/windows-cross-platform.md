---
status: resolved
trigger: "Validate and fix the macOS-developed repository so its documented functionality works on Windows."
created: 2026-07-12
updated: 2026-07-12
---

# Debug Session: windows-cross-platform

## Symptoms

- Expected behavior: A clean checkout of `codex/phase-06-gantt` can use every documented local workflow on Windows, including the portable Gantt launcher, Python server, exports/backups, and desktop packaging entry points.
- Actual behavior: Unknown at intake; establish the Windows baseline and capture each failing command before modifying code.
- Error messages: None supplied; collect from native Windows execution.
- Timeline: The repository was developed and previously verified on macOS; Windows compatibility has not yet been verified on this machine.
- Reproduction: Follow the repository documentation and execute each supported entry point from `D:\Documents\Dev` using Windows-native Python and PowerShell/cmd.

## Current Focus

- hypothesis: Confirmed and fixed: repository-relative response paths rejected external desktop data, POSIX shebang execution failed on Windows, batch error handling was expanded too early, and PyInstaller missed dynamically loaded module dependencies.
- test: Windows unit tests plus real BAT/PowerShell launchers, browser UI, portable backup, WSL path handoff, and a freshly built packaged EXE.
- expecting: All local Windows entry points serve the Gantt and persist autosaves; orchestration uses the active Python interpreter; native Plane commands fail clearly when prerequisites are absent.
- next_action: fixed and verified

## Evidence

- timestamp: 2026-07-12T07:39:01+08:00
  finding: GET `/gantt.html` and `/api/gantt-portable/latest?t=1` returned 200 from a Windows temp directory, but POST `/api/gantt-autosave` disconnected with `ValueError` from `timestamped_path.relative_to(ROOT_DIR)`.
- timestamp: 2026-07-12T07:41:00+08:00
  finding: Direct subprocess execution of `plane-api-comment.py`, `bootstrap-plane-visual-constructs.py`, and `export-plane-timeline.sh` each failed on Windows with `[WinError 193] %1 is not a valid Win32 application`.
- timestamp: 2026-07-12T07:39:12+08:00
  finding: Portable export and backup dry-run both passed when input/output paths contained spaces outside the repository (65 tasks, 67 events).
- timestamp: 2026-07-12T07:50:00+08:00
  finding: The Windows BAT launcher initially misdetected installed `python.exe` because `%errorlevel%` inside a parenthesized block was expanded before `where python` ran; changed to runtime `if not errorlevel 1` checks.
- timestamp: 2026-07-12T07:52:00+08:00
  finding: Both committed `start-windows.bat` and `start-windows.ps1` launchers served `gantt.html` with HTTP 200 from an unrelated working directory.
- timestamp: 2026-07-12T07:56:00+08:00
  finding: In-app browser loaded the Windows-served Gantt with 65 tasks, 67 markers, all 12 toolbar controls, SVG timeline content, and no console errors.
- timestamp: 2026-07-12T08:01:00+08:00
  finding: PyInstaller 6.21 built the Windows EXE; first run exposed missing hidden imports for dynamically loaded server code (`ModuleNotFoundError: json`), which were added to the spec.
- timestamp: 2026-07-12T08:03:00+08:00
  finding: Rebuilt 9,123,164-byte `PlaneDemandHubGantt.exe` served HTTP 200 and persisted autosave HTTP 200 to a Windows data path containing spaces outside the repository.
- timestamp: 2026-07-12T08:04:00+08:00
  finding: Six Windows compatibility tests pass, Python compileall passes, portable backup dry-run passes, PowerShell launcher parses, and WSL resolves the Plane installer directory.
- timestamp: 2026-07-12T08:08:00+08:00
  finding: Windows `core.autocrlf=true` initially produced CRLF worktree copies of `.sh` files and WSL Bash rejected them; added `.gitattributes` to enforce LF for Shell scripts and CRLF for native Windows launchers, then all four tracked Shell scripts passed `bash -n`.

## Eliminated


## Resolution

- root_cause: POSIX process-launch assumptions, repository-relative runtime path assumptions, cmd.exe parse-time `%errorlevel%` expansion, cwd-dependent packaging, and unlisted dependencies of dynamically loaded frozen modules.
- fix: Use `sys.executable` for Python child tools; add native Python Plane health/timeline commands and a WSL setup wrapper; make API response paths safe outside the repo; harden Windows launchers; enforce cross-platform line endings; resolve packaging from `SPEC` and declare hidden imports; add Windows documentation and regression tests.
- verification: 6/6 unit tests; BAT and PowerShell HTTP 200; browser UI 65 tasks/67 events with no console errors; portable backup dry-run success; packaged EXE HTTP 200 plus autosave HTTP 200.
- files_changed: `.gitattributes`, `scripts/serve-delivery-dashboard.py`, `scripts/progress-to-plane.py`, `scripts/apply-plane-daily-record.py`, `scripts/export-plane-timeline.py`, `scripts/plane-health.py`, `scripts/export-gantt-portable.py`, `portable/gantt/latest/`, `plane-selfhost/setup.ps1`, `packaging/plane-demand-hub-gantt.spec`, `docs/`, `tests/test_windows_compat.py`.
