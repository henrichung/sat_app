# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sat_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/config.json', 'config'),
        ('sat_app/assets', 'sat_app/assets'),
    ],
    hiddenimports=[
        'PIL', 'PIL._imagingft', 'PIL._imaging', 'PIL._imagingtk', 'PIL._tkinter_finder',
        'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
        'reportlab.lib.utils', 'reportlab.lib.colors', 'reportlab.lib.styles', 
        'reportlab.pdfbase', 'reportlab.pdfbase.ttfonts', 'reportlab.platypus',
        'matplotlib.backends.backend_agg',
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip'
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=['runtime-hooks/pil_import_hook.py'],
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
    [],
    exclude_binaries=True,
    name='SAT App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='sat_app/assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sat_app',
)