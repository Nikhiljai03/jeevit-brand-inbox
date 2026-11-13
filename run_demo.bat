@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (set "PYTHON_CMD=py -3") else (set "PYTHON_CMD=python")
%PYTHON_CMD% -m brand_inbox analyze --out artifacts\run
if errorlevel 1 exit /b 1
%PYTHON_CMD% -m brand_inbox evaluate --strict
if errorlevel 1 exit /b 1
echo.
echo Done. Open artifacts\run\report.html or artifacts\run\summary.md.
echo This demo used offline rules, not a live AI model.
