#!/usr/bin/env python3
"""
Create a simple PyInstaller spec file for SAT App with PyQt6
"""
import os
import sys

def main():
    """Create a PyInstaller spec file for building SAT App with PyQt6"""
    # Get project directory
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Important paths
    main_py = os.path.join(project_dir, "sat_app", "main.py").replace("\\", "/")
    fix_pil = os.path.join(project_dir, "tools", "fix_pil.py").replace("\\", "/")
    config_json = os.path.join(project_dir, "config", "config.json").replace("\\", "/")
    assets_dir = os.path.join(project_dir, "sat_app", "assets").replace("\\", "/")
    icon_ico = os.path.join(project_dir, "sat_app", "assets", "icon.ico").replace("\\", "/")
    
    # Runtime hooks
    runtime_hooks_str = "[]"  # Default to empty list
    hook_path = os.path.join(project_dir, "tools", "runtime-hooks", "pil_import_hook.py")
    if os.path.exists(hook_path):
        hook_path_clean = hook_path.replace("\\", "/")
        runtime_hooks_str = f"[r'{hook_path_clean}']"
        print(f"Found runtime hook: {hook_path}")
    
    # Create the spec file content
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [r'{0}', r'{1}'],
    pathex=[r'{2}'],
    binaries=[],
    datas=[
        (r'{3}', 'config'),
        (r'{4}', 'sat_app/assets'),
    ],
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.JpegImagePlugin', 'PIL.PngImagePlugin',
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip',
        'PyQt6.QtPrintSupport', 'PyQt6.QtSvg', 'PyQt6.QtNetwork',
        'fuzzywuzzy', 'fuzzywuzzy.fuzz', 'fuzzywuzzy.process', 'Levenshtein'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks={5},
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
    icon=r'{6}',
)
""".format(
    main_py,              # {0}
    fix_pil,              # {1}
    project_dir,          # {2}
    config_json,          # {3}
    assets_dir,           # {4}
    runtime_hooks_str,    # {5}
    icon_ico              # {6}
)
    
    # Write the spec file
    spec_path = os.path.join(project_dir, "tools", "simple_pyqt6.spec")
    with open(spec_path, "w") as f:
        f.write(spec_content)
    
    print(f"Created PyInstaller spec file at {spec_path}")
    print("To build the application, run:")
    print(f"python -m PyInstaller {spec_path}")

if __name__ == "__main__":
    main()