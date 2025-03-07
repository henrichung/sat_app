#!/usr/bin/env python3
"""
Script to collect PyQt6 files for PyInstaller
"""
import os
import sys
import shutil
import PyQt6

def convert_path(path):
    """Convert backslashes to forward slashes in paths"""
    return path.replace('\\', '/')

def main():
    """Collect PyQt6 files and copy them to a temporary directory"""
    # Get PyQt6 path
    pyqt6_path = os.path.dirname(PyQt6.__file__)
    print(f"PyQt6 path: {pyqt6_path}")
    
    # Create directory for collection
    script_dir = os.path.dirname(os.path.abspath(__file__))
    collect_dir = os.path.join(script_dir, "pyqt6_collect")
    print(f"Collecting PyQt6 files to: {collect_dir}")
    
    # Clean directory if it exists
    if os.path.exists(collect_dir):
        shutil.rmtree(collect_dir)
    os.makedirs(collect_dir, exist_ok=True)
    
    # Copy entire PyQt6 directory to ensure all modules are included
    print(f"Copying all PyQt6 modules from {pyqt6_path}...")
    for item in os.listdir(pyqt6_path):
        source = os.path.join(pyqt6_path, item)
        target = os.path.join(collect_dir, item)
        
        if os.path.isdir(source):
            shutil.copytree(source, target)
            print(f"Copied directory {item} to {target}")
        else:
            shutil.copy2(source, target)
            print(f"Copied file {item} to {target}")
    
    print("All PyQt6 files copied successfully")
    
    # Get absolute paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sat_app_main = convert_path(os.path.join(base_dir, "sat_app", "main.py"))
    fix_pil_path = convert_path(os.path.join(base_dir, "tools", "fix_pil.py"))
    config_json = convert_path(os.path.join(base_dir, "config", "config.json"))
    assets_dir = convert_path(os.path.join(base_dir, "sat_app", "assets"))
    icon_path = convert_path(os.path.join(base_dir, "sat_app", "assets", "icon.ico"))
    collect_dir_abs = convert_path(os.path.abspath(collect_dir))
    
    # Check for runtime hooks
    runtime_hooks_dir = os.path.join(base_dir, "runtime-hooks")
    pil_hook_path = os.path.join(runtime_hooks_dir, "pil_import_hook.py")
    
    # Build runtime hooks list
    runtime_hooks = []
    if os.path.exists(pil_hook_path):
        runtime_hooks.append(convert_path(pil_hook_path))
        print(f"Found runtime hook: {pil_hook_path}")
    
    # Create spec file with correct path
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [r'{sat_app_main}', r'{fix_pil_path}'],
    pathex=[r'{base_dir}'],
    binaries=[],
    datas=[
        (r'{config_json}', 'config'),
        (r'{assets_dir}', 'sat_app/assets'),
        (r'{collect_dir_abs}', 'PyQt6'),
    ],
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.JpegImagePlugin', 'PIL.PngImagePlugin',
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip',
        'PyQt6.QtPrintSupport', 'PyQt6.QtSvg', 'PyQt6.QtNetwork'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[{', '.join([f"r'{path}'" for path in runtime_hooks]) if runtime_hooks else ''}],
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
    icon=r'{icon_path}',
)
"""
    
    # Write spec file
    spec_path = os.path.join(os.path.dirname(collect_dir), "pyqt6_build.spec")
    with open(spec_path, "w") as f:
        f.write(spec_content)
    
    print(f"Created PyInstaller spec file at {spec_path}")
    print("To build the application, run:")
    print(f"python -m PyInstaller {spec_path}")

if __name__ == "__main__":
    main()