@echo off
setlocal enableextensions

REM Change to the directory of this script
pushd "%~dp0"

REM Prefer the Python launcher on Windows
set "PY=py -3"

REM Launch only the main bot in a separate terminal window and keep it open
start "run_bot1" cmd /k %PY% run_bot1.py

popd
endlocal
