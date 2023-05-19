@echo off

if not exist .\.venv\installed (
    echo done > .\.venv\installed
    echo.
    echo Upgrading PIP . . .
    python -m pip install --upgrade pip
    echo    done.

    echo Installing dependencies . . .
    pip install -r requirements.txt
)
