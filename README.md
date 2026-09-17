# YuE2 Web UI Lite

Local web panel (Gradio) for autoregressive song synthesis with YuE2-3B:
Text2Music and Score Editor. Server: `127.0.0.1:9099`.

Voice conversion and Cover mode are available in the FULL version.

## Launch

```bat
start_webui.bat
```

The model loads into VRAM once at startup.

## Requirements

- NVIDIA GPU, CUDA (PyTorch cu121/cu126/cu128 - channel depends on GPU series).
- VRAM: 24 GB recommended; 16 GB supported (auto-chunked synthesize, slower render); <12 GB not supported.
- Windows; Python venv with all dependencies, model cache in `hf_cache/`.

## Support matrix

| GPU | Compute cap | Profile | Status |
|---|---|---|---|
| RTX 30 / 40 | 8.6 / 8.9 | P1 (cu121) | fully tested |
| RTX 50 | 10.0 / 12.0 | P2 (cu128) | experimental |
| other | <8.6 | P1 + warning | not tested |

VRAM classes: >=24 GB recommended, >=16 GB supported, >=12 GB experimental
(requires `YUE2_ALLOW_12GB=1` before setup.bat), <12 GB not supported.

## Manual presets

`setup.bat /manual` opens numbered presets:

| # | Preset | series | ch_main |
|---|---|---|---|
| 1 | RTX 30 | 30 | cu121 |
| 2 | RTX 40 | 40 | cu121 |
| 3 | RTX 50 | 50 | cu128 |
| 4 | Other/older | other | cu121 |

Then VRAM class: 1) Auto, 2) 24 GB, 3) 16 GB, 4) 12 GB experimental.
Scriptable mode: `YUE2_MANUAL_MODE` + optional `YUE2_MANUAL_SERIES/_CH_MAIN/_VCLASS`.

## Cache hygiene

The installer writes nothing to disk C. `pip_cache/`, `.meta/` and `.tmp/`
stay inside the distribution folder. After a successful install `pip_cache/`
and `.meta/` may be removed.

## Resume behavior

Re-running `setup.bat` is safe: every step is idempotent. Network step 3
(torch) uses a 2-strike retry; local steps do not retry.

## Features

- **Text2Music** - text + style -> track (cot: full/melody/no score, ODE steps, seed).
- **Score Editor (Advanced)** - edit the ABC score of the last track and re-render
  without regenerating the composition.

When VRAM is low the synthesizer automatically falls back to chunking
(single -> tiling -> chunked with OOM retry). Use `YUE2_VRAM_LIMIT_GB` to
emulate a weaker GPU.

## AI mechanic

See `SUPPORT_AGENT.md` / `SUPPORT_AGENT_RU.md` for diagnostics and the F1-Fx playbook.
