@echo off
:: run_tests.bat [pytest args]
::   Run unit tests, e.g. "run_tests.bat -v" or "run_tests.bat -k doxy_py_checker"

pushd "%~dp0.."
poetry run pytest %*
set EXIT_CODE=%errorlevel%
popd
pause
exit /b %EXIT_CODE%
