@echo off
rem Main YuE2 Web UI launcher (port 9099). Requires setup.bat to be run once.
rem Temp hygiene: TMP/TEMP/GRADIO_TEMP_DIR inside the dist - nothing on C:.
cd /d %~dp0
set "TMP=%~dp0.tmp"
set "TEMP=%~dp0.tmp"
set "GRADIO_TEMP_DIR=%~dp0.tmp\gradio"
if not exist "%~dp0.tmp\gradio" mkdir "%~dp0.tmp\gradio"
python\python.exe app.py
pause
