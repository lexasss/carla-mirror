@echo off

if not exist .venv/ (
    echo Please wait . . .
    python -m venv .\.venv
    echo.
    echo Please run `install.bet`
)

.\.venv\Scripts\activate
