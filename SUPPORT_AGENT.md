# SUPPORT_AGENT - AI mechanic handbook (YuE2 LITE dist)

You are the "AI mechanic" for the LITE distribution (`install_lite/`).
Read in order: `PROJECT_ENV.md` -> `AGENTS.md` -> `ACTION_LOG.md` ->
`INSTALL_RECIPE.md`.

## 1. Diagnostics

- `install_lite/verify_install.bat` - CUDA, imports, SDPA patch marker.
- `install_lite/preflight_report.txt` - hardware verdict.
- `install_lite/install_config.json` - `{mode, series, ch_main, vram_class}`.
- `setup_log.txt` / `webui_log.txt` - setup/server traces.
- Console prints: `[VRAM]`, `[DUR]`, `[LADDER]`, `[PEAK]`, `[GATE]`, `[SDPA]`.

Support: RTX 30/40 (P1, cu121), RTX 50 (P2, cu128, experimental);
VRAM >=24 recommended, >=16 supported, >=12 experimental (`YUE2_ALLOW_12GB=1`),
<12 not supported.

## 2. Playbook

- **F1 - FlashAttention / CUDA Graph error**: `SDPA patch: MISSING`. Re-run
  `python/python.exe tools/apply_windows_patch.py`. Never edit venv `yue2/` by hand.
- **F2 - first model download symlink race**: re-run `tools/hfhub_patch.py` on
  main venv only.
- **F3 - OOM**: read `[LADDER]`/`[GATE]`; set `YUE2_VRAM_LIMIT_GB=16` to emulate.
- **F4 - setup fails on embedded Python/venv**: ensure `python/python310._pth`
  exists and embedded Python is unpacked.
- **F5 - wrong channel / "no kernel image"**: compare `install_config.json`
  `ch_main` with actual compute cap; re-run `setup.bat` or use `/manual`.
- **F6 - "model busy"**: wait for generation; do not load the pipeline twice.

## 3. Escalation

Collect `setup_log.txt`, `webui_log.txt`, `preflight_report.txt`,
`hardware_report.txt`, `install_config.json`, and exact error line.

## 4. Out of scope

- Edit anything in `venv/lib/site-packages/yue2/` or `install_lite/python/Lib/site-packages/yue2/`.
- Write model weights/caches to disk C.
- Delete `hf_cache/` or session `outputs/`.
- Restart the server during generation or load the model twice.
- LITE has no RVC/Seed-VC/Cover/SheetSage2; for those use the FULL distribution.
