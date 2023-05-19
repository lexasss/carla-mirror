@echo off

if not exist .venv/ (
    rem python -m venv .\.venv
    echo.
    echo Please run `install.bet`
)

.\.venv\Scripts\activate
