# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path.cwd()

DATA_FILES = [
    "scripts/serve-delivery-dashboard.py",
    "scripts/export-gantt-portable.py",
    "scripts/build-delivery-dashboard.py",
    "portable/gantt/latest/README.md",
    "portable/gantt/latest/gantt-local-edits.json",
    "portable/gantt/latest/gantt.html",
    "portable/gantt/latest/gantt.json",
    "portable/gantt/latest/manifest.json",
    "portable/gantt/latest/start-macos-linux.sh",
    "portable/gantt/latest/start-windows.bat",
    "portable/gantt/latest/start-windows.ps1",
]

datas = [(str(ROOT / item), str(Path(item).parent)) for item in DATA_FILES]

a = Analysis(
    [str(ROOT / "scripts/gantt_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PlaneDemandHubGantt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
