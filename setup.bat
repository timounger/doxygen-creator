@echo off
:: setup.bat
::   Install the package (editable) with all extras (dev: pytest).

:: In CI (CI=true on GitHub runners) validate the committed lockfile instead of
:: regenerating it: an out-of-date poetry.lock fails the build (reproducible installs).
:: Locally the lock is (re)generated for convenience.
if "%CI%"=="true" (
    poetry check --lock
    if errorlevel 1 exit /b 1
) else (
    poetry lock
)
poetry sync --all-extras
::pause
