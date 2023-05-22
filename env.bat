@echo off

if not exist .venv/ (
    echo Please wait . . .
    python -m venv .\.venv
    echo.
    echo Please run `install.bat`
)

start "CARLA scripting" .\.venv\Scripts\activate
