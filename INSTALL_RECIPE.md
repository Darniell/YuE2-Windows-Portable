# INSTALL_RECIPE - YuE2 LITE portable distribution (install_lite/)

Extract `install_lite/` to any folder, run `setup.bat`, then `verify_install.bat`,
then `start_webui.bat`.

LITE includes only Text2Music and Score Editor. Voice conversion and Cover mode
are available in the FULL version.

## 1. Hardware preflight

`setup.bat` (auto) runs `tools/preflight.py --auto`:
- nvidia-smi -> compute cap, VRAM, driver
- disk free >= 20 GB
- RAM >= 16 GB

BLOCK conditions: no NVIDIA GPU, driver below channel minimum, <20 GB free disk,
<12 GB VRAM.

## 2. Manual presets

`setup.bat /manual` asks:
1. Preset (1-4): sets `series` and `ch_main`.
2. VRAM class (1-4): sets `vram_class`.
3. Summary: 1) Apply / 2) Start over.

Config written to `install_config.json`: `{mode, series, ch_main, vram_class}`.

## 3. Setup steps (6 steps)

1. **Python** - unpack `tools/python-3.10.11-embed-amd64.zip` to `python/`, write `python310._pth`.
2. **Preflight** - hardware check, write `install_config.json`.
3. **pip** - `get-pip.py` + upgrade pip/setuptools/wheel/virtualenv.
4. **torch** - install from PyTorch index per profile.
5. **main freeze** - `dist_freeze/requirements-main-freeze.txt` with `--no-deps`.
6. **yue2 wheel + SDPA patch** - install local wheel, apply Windows SDPA patch.
7. **hfhub patch** - patch `huggingface_hub` in main venv only.

Re-running `setup.bat` is safe: every step is idempotent. Network step 3 retries
once on first failure.

## 4. Cache hygiene

Before any pip/virtualenv call setup.bat sets:
- `PIP_CACHE_DIR=<dist>\pip_cache`
- `VIRTUALENV_APP_DATA=<dist>\.meta\virtualenv`
- `TMP`/`TEMP=<dist>\.tmp`

Nothing is written to disk C.

## 5. Verify

`verify_install.bat` checks:
- SDPA patch marker in `yue2/cuda_graph.py`
- `import torch; torch.cuda.is_available()`
- `import yue2, gradio`
- profile printed to `hardware_report.txt`
