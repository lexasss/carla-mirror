@echo off

if not exist .venv/ (
    echo Please wait . . .
    python -m venv .\.venv
    echo.
    echo Please run `install.bat`
)

if "%TERM_PROGRAM%" neq "" (
    rem We do not need a separate window when running from the VS Code environment
    .\.venv\Scripts\activate
) else (
    start "CARLA script" .\.venv\Scripts\activate
)