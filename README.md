# YuE2 Windows Portable — AI Song Studio on Your Own PC

Full songs from lyrics, score editing, covers, and voice conversion — on Windows, offline after the first setup, on NVIDIA GPUs from 12 GB VRAM[cite: 4]. No Docker, no Linux, no conda[cite: 4].

[YouTube Demo](#) • [Boosty — Extended Edition](#) • [Hugging Face](#) • [Releases](#) • [🇷🇺 Русская версия](README_ru.md)

## A Personal Note First
I'm saving up to bring my fiancée from the Philippines to my country — visa paperwork and relocation cost more than I can earn quickly. So this project is my honest fundraiser: **the Basic edition is free here, forever**, and the **Extended edition** (cover mode + one-click RVC/Seed-VC voice conversion) funds the goal on Boosty. When the goal is reached, everything that is on Boosty today will go public on these pages. No paywalled knowledge — just a head start for those who want to help.

## What It Is
A zero-config Windows packaging of YuE2 and friends that simply works:
- **Tab 1 — Text → Song:** lyrics + style prompt → complete song (vocals + instruments); confident singing in RU/EN/ZH/JA/KO/ES[cite: 4].
- **Tab 2 — Score Editor:** rerender the ABC score with a new style, tempo, or seed without regenerating the composition[cite: 4].
- **Tab 3 — Cover (Extended):** any MP3 → melody + lyrics transcription (SheetSage2 + faster-whisper) → cover in a new style.
- **Voice Conversion (Extended):** RVC (trained voices) and Seed-VC (zero-shot from a 10–30 s reference clip).
- **VRAM Ladder:** auto tiling/chunking — 24 GB+ recommended, 16 GB supported, 12 GB experimental[cite: 4].
- **Installer:** embedded Python 3.10, fully pinned freezes, portable ffmpeg, offline RVC base weights, resumable gated setup with logs[cite: 3].

## Editions
| Feature | Basic — Free (This Repo) | Extended — Boosty |
|---|---|---|
| Text→Song + Score Editor[cite: 4] | ✅ | ✅ |
| Cover mode (Tab 3) | — | ✅ |
| RVC + Seed-VC auto-installer | — | ✅ |
| Installer (`setup.bat`)[cite: 3] | Lite menu | Full menu (VC) |

*Once the fiancée goal is reached, the Extended build is published here as a public release.*

## Quick Start
1. Download `YuE2-Lite-Portable.zip` from [Releases](https://github.com/Darniell/YuE2-Windows-Portable/releases).
2. Extract it anywhere (do **not** use `Program Files`).
3. Run `setup.bat` (Auto or Manual preset)[cite: 3].
4. Run `verify_install.bat` → `start_webui.bat` → open `http://127.0.0.1:9099`[cite: 3, 4].
5. First launch downloads YuE2 weights (~8 GB) from official Hugging Face repos under their original licenses[cite: 4].

## Requirements & Support Matrix
- **OS:** Windows 10/11 x64[cite: 4].
- **GPU:** NVIDIA GPU with CUDA[cite: 4].
- **VRAM:** 24 GB+ recommended; 16 GB supported (auto-chunked synthesize, slower render); 12 GB experimental (requires `YUE2_ALLOW_12GB=1`)[cite: 4]. *Note: There is a possibility of running it on an 11 GB RTX 2080 Ti.*
- **Disk:** ~15–40 GB free space.

| GPU Series | Compute Cap | Profile | Status |
|---|---|---|---|
| RTX 30 / 40[cite: 4] | 8.6 / 8.9[cite: 4] | P1 (cu121)[cite: 4] | fully tested[cite: 4] |
| RTX 50[cite: 4] | 10.0 / 12.0[cite: 4] | P2 (cu128)[cite: 4] | experimental[cite: 4] |
| Other[cite: 4] | <8.6[cite: 4] | P1 + warning[cite: 4] | not tested[cite: 4] |

## Troubleshooting & Support
If you encounter errors during setup or generation, check out **[HELP_TROUBLESHOOTING_EN.md](HELP_TROUBLESHOOTING_EN.md)**. It explains how to use a free AI agent (like Verdent) to automatically read your logs and fix the installation using the built-in system playbook (`SUPPORT_AGENT.md`)[cite: 5].

## Manual Presets
`setup.bat /manual` opens numbered presets:
1. RTX 30 (`series: 30`, `ch_main: cu121`)[cite: 4]
2. RTX 40 (`series: 40`, `ch_main: cu121`)[cite: 4]
3. RTX 50 (`series: 50`, `ch_main: cu128`)[cite: 4]
4. Other/older (`series: other`, `ch_main: cu121`)[cite: 4]

## Cache Hygiene & Architecture
- **No disk C clutter:** The installer writes nothing to disk C. `pip_cache/`, `.meta/`, and `.tmp/` stay inside the distribution folder[cite: 3].
- **Idempotent setup:** Re-running `setup.bat` is safe. Network step 3 uses a 2-strike retry[cite: 3].
- **Under the hood:** Embedded Python 3.10.11 · pinned `--no-deps` freezes · Windows SDPA patch for yue2 · huggingface-hub symlink-race patch[cite: 3].

## Upstream & Licenses
This repository ships tooling and installers only — **no model weights**. YuE2, SheetSage2, RVC, Seed-VC, demucs, faster-whisper, and ffmpeg remain property of their authors; weights are downloaded from official repositories at first launch under their original licenses. Packaging code: MIT.

## Support
Boosty (Extended + updates) • YouTube Demo • ⭐ Stars and shares move the fiancée goal directly. Thank you!
