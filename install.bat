@echo off

if not exist .\.venv\installed (
    echo done > .\.venv\installed
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)
