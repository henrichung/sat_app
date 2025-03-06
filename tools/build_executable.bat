@echo off

REM Ensure pyinstaller is installed
pip install pyinstaller

REM Build the standalone executable
pyinstaller sat_app.spec

echo Standalone application built in dist\sat_app directory.