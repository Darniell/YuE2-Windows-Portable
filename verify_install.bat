@echo off
rem Self-verification after LITE setup: Windows SDPA patch + CUDA + main imports.
cd /d %~dp0

set "SDPA_STATE=MISSING"
powershell -NoProfile -Command "if (Select-String -Path python\Lib\site-packages\yue2\cuda_graph.py -Pattern 'SDPA-WIN-PATCH' -Quiet) { exit 0 } else { exit 1 }"
if not errorlevel 1 set "SDPA_STATE=applied"
echo SDPA patch: %SDPA_STATE%
if "%SDPA_STATE%"=="MISSING" (
    echo ERROR: Windows SDPA patch is MISSING. Generation would crash on Windows.
    echo Re-run setup.bat, or manually: python\python.exe tools\apply_windows_patch.py
    pause
    exit /b 1
)

python\python.exe -c "import torch; print('CUDA:', torch.cuda.is_available()); import yue2, gradio; print('All imports OK')"
if %errorlevel% neq 0 (
    echo ERROR: setup not complete. Run setup.bat first.
    pause
    exit /b 1
)

if exist install_config.json (
    python\python.exe tools\profile.py print > hardware_report.txt
    type hardware_report.txt
) else (
    echo Profile: legacy install, no install_config.json - main cu121 assumed
    echo Profile: legacy install, no install_config.json - main cu121 assumed> hardware_report.txt
)

echo Verification passed!
pause
