@echo off
:: run_example.bat
::   Create doxygen documentation of this repository with examples/create_doxygen.py and open it.

pushd "%~dp0"
IF EXIST "Output_Doxygen" (
    rmdir /s /q "Output_Doxygen"
)
poetry run python create_doxygen.py -o
set EXIT_CODE=%errorlevel%
popd
pause
exit /b %EXIT_CODE%
