# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['sat_app\\main.py', 'tools\\fix_pil.py'],
    pathex=[],
    binaries=[],
    datas=[('config/config.json', 'config'), ('sat_app/assets', 'sat_app/assets')],
    hiddenimports=['PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.JpegImagePlugin', 'PIL.PngImagePlugin'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6', 'PySide6'],
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
    name='SAT App',
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
    icon=['sat_app\\assets\\icon.ico'],
)
