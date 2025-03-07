@echo off
echo === SAT App Build Process with PyQt6 ===
echo.

echo Step 1: Cleaning PyQt environment...
python tools\clean_pyqt_env.py
echo.

echo Step 2: Collecting PyQt6 files and generating spec...
python tools\collect_pyqt6.py
echo.

echo Step 3: Building application with PyInstaller...
python -m PyInstaller tools\pyqt6_build.spec
echo.

echo Build completed successfully!
echo The executable should be located in the dist folder.
echo.