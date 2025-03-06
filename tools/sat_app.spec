# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files
data_files = [
    ('config/config.json', 'config'),
    ('sat_app/assets', 'sat_app/assets'),
]

# Add data directories if they exist
if os.path.exists('data/images'):
    data_files.append(('data/images', 'data/images'))
if os.path.exists('data/worksheets'):
    data_files.append(('data/worksheets', 'data/worksheets'))

# Include all needed modules
hidden_imports = collect_submodules('matplotlib')
hidden_imports.extend(collect_submodules('numpy'))
hidden_imports.extend(collect_submodules('PyQt6'))
hidden_imports.extend(collect_submodules('reportlab'))
hidden_imports.extend(collect_submodules('sympy'))
hidden_imports.extend(['PIL', 'PyPDF2'])

a = Analysis(
    ['sat_app/main.py'],
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    icon='sat_app/assets/icon.ico' if os.path.exists('sat_app/assets/icon.ico') else None,
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

# For macOS
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='SAT App.app',
        icon='sat_app/assets/icon.icns' if os.path.exists('sat_app/assets/icon.icns') else None,
        bundle_identifier=None,
    )