# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../../sat_app/sat_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../config/config.json', 'config'),
        ('sat_app/assets', 'sat_app/assets'),
        ('E:\Projects\sat_app\tools\pyqt6_collect', 'PyQt6'),
    ],
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.JpegImagePlugin', 'PIL.PngImagePlugin',
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip',
        'PyQt6.QtPrintSupport', 'PyQt6.QtSvg', 'PyQt6.QtNetwork'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
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
    icon='sat_app/assets/icon.ico',
)
