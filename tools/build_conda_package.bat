@echo off
setlocal

REM Ensure conda-build is available
call conda install -y conda-build

REM Build the conda package
call conda build conda-recipe

REM Get the path to the built package
for /f "tokens=*" %%a in ('call conda build conda-recipe --output') do set PKG_PATH=%%a
echo Package built at: %PKG_PATH%

REM Optional: Convert to packages for other platforms
REM call conda convert --platform all %PKG_PATH% -o outputdir\

echo To install the package run:
echo conda install %PKG_PATH%

endlocal