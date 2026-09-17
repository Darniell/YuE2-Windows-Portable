@echo off
rem YuE2 LITE setup orchestrator (idempotent): only main venv + yue2.
rem Text2Music + Score Editor only.
rem 6 steps: 1 unpack, 1.5 preflight, 2 pip, 3 torch, 4 freeze, 5 yue2+SDPA, 6 hfhub patch.
rem Interactive input happens BEFORE the tee relay.
setlocal
cd /d %~dp0

rem Child phase (relaunched under tee) skips the menus.
if defined YUE2_SETUP_TEE goto tee_ready

set "ASK_BUF="
set "ASK_FAILS=0"
set "MODE_SEL="
if /i "%~1"=="/manual" set "MODE_SEL=2"

rem ---- Menu 1: Auto-detect vs Manual presets ----
:menu1
echo === YuE2 LITE setup: configuration ===
echo   1^) Auto-detect (recommended)
echo   2^) Manual presets
if defined MODE_SEL goto menu1_check
call :ask MODE_SEL "Choice [1/2]: "
if errorlevel 2 goto input_abort
:menu1_check
if "%MODE_SEL%"=="1" (
    echo Auto-detect selected: preflight will pick the profile.
    goto parent_done
)
if "%MODE_SEL%"=="2" goto menu2
echo Invalid choice: "%MODE_SEL%" - enter 1 or 2.
set "MODE_SEL="
goto menu1

rem ---- Menu 2: GPU preset = series + main channel ----
:menu2
echo === Manual presets ===
echo   1^) RTX 30 - cu121 (fully tested)
echo   2^) RTX 40 - cu121 (fully tested)
echo   3^) RTX 50 - cu128 (experimental)
echo   4^) Other/older - cu121 (untested)
call :ask PRESET "Preset [1-4]: "
if errorlevel 2 goto input_abort
if "%PRESET%"=="1" (
    set "SERIES=30"
    set "CH_MAIN=cu121"
    set "PRESET_NAME=RTX 30 cu121"
    goto menu3
)
if "%PRESET%"=="2" (
    set "SERIES=40"
    set "CH_MAIN=cu121"
    set "PRESET_NAME=RTX 40 cu121"
    goto menu3
)
if "%PRESET%"=="3" (
    set "SERIES=50"
    set "CH_MAIN=cu128"
    set "PRESET_NAME=RTX 50 cu128"
    goto menu3
)
if "%PRESET%"=="4" (
    set "SERIES=other"
    set "CH_MAIN=cu121"
    set "PRESET_NAME=Other older cu121"
    goto menu3
)
echo Invalid choice: "%PRESET%" - enter 1, 2, 3 or 4.
goto menu2

rem ---- Menu 3: VRAM class ----
:menu3
set "VRAM_MB="
set "VRAM_GB="
for /f "usebackq delims=" %%G in (`nvidia-smi --query-gpu^=memory.total --format^=csv^,noheader^,nounits 2^>nul`) do (
    if not defined VRAM_MB set "VRAM_MB=%%G"
)
if defined VRAM_MB (
    echo %VRAM_MB%| findstr /r /c:"^[0-9][0-9]*$" >nul && set /a VRAM_GB=^(VRAM_MB+512^)/1024
)
set "VRAM_AUTO_CLASS=recommended"
if not defined VRAM_GB goto menu3_class_done
if %VRAM_GB% GEQ 24 goto menu3_class_done
if %VRAM_GB% GEQ 16 (set "VRAM_AUTO_CLASS=supported") else set "VRAM_AUTO_CLASS=experimental"
:menu3_class_done
echo === VRAM class ===
if defined VRAM_GB (
    echo   Detected: %VRAM_GB% GB
    echo   1^) Auto ^(detected: %VRAM_GB% GB - class %VRAM_AUTO_CLASS%^)
) else (
    echo   Detected: unknown ^(nvidia-smi unavailable^)
    echo   1^) Auto ^(detection failed - class recommended^)
)
echo   2^) 24 GB class recommended
echo   3^) 16 GB class supported
echo   4^) 12 GB class experimental (needs YUE2_ALLOW_12GB=1)
call :ask VRAM_SEL "VRAM class [1-4]: "
if errorlevel 2 goto input_abort
if "%VRAM_SEL%"=="1" (
    set "VRAMCLASS=%VRAM_AUTO_CLASS%"
    goto summary
)
if "%VRAM_SEL%"=="2" (
    set "VRAMCLASS=recommended"
    goto summary
)
if "%VRAM_SEL%"=="3" (
    set "VRAMCLASS=supported"
    goto summary
)
if "%VRAM_SEL%"=="4" (
    set "VRAMCLASS=experimental"
    goto summary
)
echo Invalid choice: "%VRAM_SEL%" - enter 1, 2, 3 or 4.
goto menu3

:summary
if defined VRAM_GB (set "VRAM_TXT=%VRAM_GB% GB") else set "VRAM_TXT=unknown"
echo === Summary ===
echo   Preset: %PRESET_NAME% ^| main %CH_MAIN% ^| VRAM: %VRAM_TXT% / %VRAMCLASS%
echo   1^) Apply   2^) Start over
call :ask APPLY "Apply? [1/2]: "
if errorlevel 2 goto input_abort
if "%APPLY%"=="1" goto apply_env
if "%APPLY%"=="2" goto menu2
echo Invalid choice: "%APPLY%" - enter 1 or 2.
goto summary

:apply_env
set "YUE2_MANUAL_MODE=1"
set "YUE2_MANUAL_SERIES=%SERIES%"
set "YUE2_MANUAL_CH_MAIN=%CH_MAIN%"
set "YUE2_MANUAL_VCLASS=%VRAMCLASS%"
set "YUE2_MANUAL_PRESET=%PRESET_NAME%"
goto parent_done

:input_abort
echo [SETUP] ERROR: no more input available - configuration aborted.
exit /b 1

:parent_done
set "ASK_BUF="
set "ASK_LINE="
set "ASK_FAILS="
goto tee_relay

:ask
if defined ASK_BUF goto ask_pop
set "ASK_LINE="
set /p ASK_LINE="%~2"
if not defined ASK_LINE goto ask_none
for /f "tokens=1,*" %%a in ("%ASK_LINE%") do (
    set "%~1=%%a"
    set "ASK_BUF=%%b"
)
goto ask_done
:ask_pop
for /f "tokens=1,*" %%a in ("%ASK_BUF%") do (
    set "%~1=%%a"
    set "ASK_BUF=%%b"
)
:ask_done
if defined %~1 exit /b 0
:ask_none
set /a ASK_FAILS+=1
if %ASK_FAILS% GEQ 5 exit /b 2
goto ask

:tee_relay
set "YUE2_SETUP_TEE=1"
powershell -NoProfile -Command "cmd /c 'setup.bat %* 2>&1' | ForEach-Object { Write-Host $_; Add-Content -Path 'setup_log.txt' -Value $_ -Encoding UTF8 }; exit $LASTEXITCODE"
exit /b %errorlevel%
:tee_ready

rem ---- Cache hygiene ----
set "PIP_CACHE_DIR=%~dp0pip_cache"
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"
set "VIRTUALENV_APP_DATA=%~dp0.meta\virtualenv"
if not exist "%VIRTUALENV_APP_DATA%" mkdir "%VIRTUALENV_APP_DATA%"
set "TMP=%~dp0.tmp"
set "TEMP=%~dp0.tmp"
if not exist "%TEMP%" mkdir "%TEMP%"

rem ---- Config mode ----
set "MODE="
if not defined YUE2_MANUAL_MODE goto after_manual
set "MODE=M"
set "SERIES=%YUE2_MANUAL_SERIES%"
if defined YUE2_MANUAL_CH_MAIN (set "CH_MAIN=%YUE2_MANUAL_CH_MAIN%") else if "%SERIES%"=="50" (set "CH_MAIN=cu128") else set "CH_MAIN=cu121"
if defined YUE2_MANUAL_VCLASS (set "VRAMCLASS=%YUE2_MANUAL_VCLASS%") else set "VRAMCLASS=recommended"
if defined YUE2_MANUAL_PRESET (set "PRESET_TXT=%YUE2_MANUAL_PRESET%") else set "PRESET_TXT=env"
echo Manual config: preset=%PRESET_TXT% (main %CH_MAIN%), vram=%VRAMCLASS%
set "CH_OK=0"
if /i "%CH_MAIN%"=="cu121" set "CH_OK=1"
if /i "%CH_MAIN%"=="cu126" set "CH_OK=1"
if /i "%CH_MAIN%"=="cu128" set "CH_OK=1"
if "%CH_OK%"=="0" (
    echo ERROR: main channel must be cu121, cu126 or cu128.
    pause
    exit /b 1
)
set "VC_OK=0"
if /i "%VRAMCLASS%"=="recommended" set "VC_OK=1"
if /i "%VRAMCLASS%"=="supported" set "VC_OK=1"
if /i "%VRAMCLASS%"=="experimental" set "VC_OK=1"
if "%VC_OK%"=="0" (
    echo ERROR: VRAM class must be recommended, supported or experimental.
    pause
    exit /b 1
)
> install_config.json echo {
>> install_config.json echo "mode": "manual",
>> install_config.json echo "series": "%SERIES%",
>> install_config.json echo "ch_main": "%CH_MAIN%",
>> install_config.json echo "vram_class": "%VRAMCLASS%"
>> install_config.json echo }
echo Config written to install_config.json.
:after_manual

echo [1/6] Unpacking embedded Python...
if not exist python\python.exe (
    powershell -NoProfile -Command "Expand-Archive -Path tools\python-3.10.11-embed-amd64.zip -DestinationPath python -Force"
)
powershell -NoProfile -Command "Set-Content python\python310._pth -Value 'python310.zip','..','.','import site'"
call :gate 1 "unpack embedded Python" || exit /b 1
if /i "%YUE2_SETUP_STOP_AFTER%"=="1" goto dry_done

echo [1.5/6] Hardware preflight...
if /i "%MODE%"=="M" (
    python\python.exe tools\preflight.py --verify-config
) else (
    python\python.exe tools\preflight.py --auto
)
if errorlevel 1 (
    echo ERROR: preflight BLOCKED the install. See preflight_report.txt.
    call :cleanup_tmp
    pause
    exit /b 1
)
call :gate 1.5 "preflight" || exit /b 1

rem Resolve torch pins AFTER preflight has written/verified install_config.json.
for /f "usebackq delims=" %%L in (`python\python.exe tools\profile.py resolve`) do set "%%L"
if errorlevel 1 (
    echo ERROR: cannot resolve install profile from install_config.json.
    call :cleanup_tmp
    pause
    exit /b 1
)
if "%VRAM_CLASS%"=="experimental" if not "%YUE2_ALLOW_12GB%"=="1" (
    echo ERROR: VRAM class is experimental ^(12 GB^). Set YUE2_ALLOW_12GB=1 to proceed.
    call :cleanup_tmp
    pause
    exit /b 1
)
echo Profile: %PROFILE% ^| main torch %MAIN_TORCH%

if /i "%YUE2_SETUP_STOP_AFTER%"=="1.5" goto dry_done

echo [2/6] Setting up pip...
if not exist python\Lib\site-packages\pip (
    python\python.exe tools\get-pip.py --no-warn-script-location
)
python\python.exe -m pip install --no-input --upgrade pip setuptools wheel virtualenv
call :gate 2 "pip + virtualenv" || exit /b 1
if /i "%YUE2_SETUP_STOP_AFTER%"=="2" goto dry_done

echo [3/6] Installing torch (profile %PROFILE%, channel %MAIN_INDEX%)...
set "STEP_TRIES=0"
:step3_retry
set /a STEP_TRIES+=1
call :do_step3
if errorlevel 1 (
    call :net_fail 3 "torch"
    if errorlevel 1 exit /b 1
    goto step3_retry
)
if /i "%YUE2_SETUP_STOP_AFTER%"=="3" goto dry_done

echo [4/6] Installing main dependencies...
python\python.exe -m pip install --no-deps --no-input -r dist_freeze\requirements-main-freeze.txt
call :gate 4 "main dependencies" || exit /b 1
if /i "%YUE2_SETUP_STOP_AFTER%"=="4" goto dry_done

echo [5/6] Installing yue2 wheel + SDPA patch...
python\python.exe -m pip install --no-deps --no-input tools\yue2_infer-0.1.5-py3-none-any.whl
call :gate 5 "yue2 wheel" || exit /b 1
python\python.exe tools\apply_windows_patch.py
if errorlevel 1 echo ERROR: Windows SDPA patch failed to apply.
call :gate 5.5 "Windows SDPA patch" || exit /b 1
if /i "%YUE2_SETUP_STOP_AFTER%"=="5" goto dry_done

echo [6/6] Patching huggingface_hub (first-run download race)...
python\python.exe tools\hfhub_patch.py python\Lib\site-packages
call :gate 6 "hfhub patch" || exit /b 1
if /i "%YUE2_SETUP_STOP_AFTER%"=="6" goto dry_done

call :cleanup_tmp
echo Setup complete! Run verify_install.bat to check.
echo Full log: setup_log.txt
pause
exit /b 0

:dry_done
echo Dry run: stopped after step %YUE2_SETUP_STOP_AFTER% (YUE2_SETUP_STOP_AFTER).
call :cleanup_tmp
exit /b 0

:cleanup_tmp
if exist "%~dp0.tmp" rmdir /s /q "%~dp0.tmp"
exit /b 0

:do_step3
python\python.exe -m pip install --no-input torch==%MAIN_TORCH% torchaudio==%MAIN_TORCHAUDIO% torchvision==%MAIN_TORCHVISION% --index-url https://download.pytorch.org/whl/%MAIN_INDEX% --extra-index-url https://pypi.org/simple
exit /b %errorlevel%

:net_fail
if "%STEP_TRIES%"=="1" (
    echo Network step failed. If your antivirus asked for permission - allow it, then press any key
    pause
    exit /b 0
)
echo [SETUP] FAILED at step %~1: %~2
echo Re-run setup.bat to resume - finished steps are skipped.
call :cleanup_tmp
pause
exit /b 1

:gate
if errorlevel 1 (
    echo [SETUP] FAILED at step %~1: %~2
    echo Re-run setup.bat to resume - finished steps are skipped.
    call :cleanup_tmp
    pause
    exit /b 1
)
exit /b 0
