# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build configuration for the Cozy Library executable.
# Includes assets, bundled data, tray dependencies, and notification backends.
from PyInstaller.utils.hooks import collect_submodules

# Include tray icon dependencies required by the packaged executable.
hiddenimports = ['pystray._base', 'pystray._win32', 'plyer.platforms.win.notification', 'plyer.platforms.win.libs.balloontip', 'plyer.platforms.win.libs.win_api_defs']
hiddenimports += collect_submodules('pystray')
hiddenimports += collect_submodules('plyer')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('data', 'data')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CozyLibrary',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\app.ico'],
)
