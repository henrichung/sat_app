@echo off
echo === Simple SAT App Build Process with PyQt6 ===
echo.

echo Step 1: Cleaning environment...
python -m pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5_sip PySide6 shiboken6
python -m pip install PyQt6==6.8.1 PyQt6-Qt6==6.8.2 PyQt6_sip==13.10.0
echo.

echo Step 2: Creating spec file...
python tools\simple_pyqt6_spec.py
echo.

echo Step 3: Building application with PyInstaller...
python -m PyInstaller tools\simple_pyqt6.spec
echo.

echo Build completed!
echo The executable should be in the dist folder.
echo.