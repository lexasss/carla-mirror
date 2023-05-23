@echo off

if not exist .venv/ (
    echo Please wait . . .
    python -m venv .\.venv
    echo.
    echo Please run `install.bat`
)

if "%TERM_PROGRAM%" neq "" (
    rem This script is running from VS Code environment,
    rem therefore we do not need a separate window
    .\.venv\Scripts\activate
) else (
    rem Otherwise there is no way (OR IS IT?) to force venv affecting the environment the script was launched from,
    rem therefore we need a separate cmd-line window
    start "CARLA script" .\.venv\Scripts\activate
    exit /b
)