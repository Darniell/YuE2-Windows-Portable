@echo off
rem Hardware preflight wrapper: run BEFORE setup.bat to see the verdict.
rem Uses the embedded python if present, otherwise any python on PATH.
cd /d %~dp0
set "PF_PY=python\python.exe"
if not exist "%PF_PY%" set "PF_PY=python"
"%PF_PY%" tools\preflight.py --auto
pause
