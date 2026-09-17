# YuE2 Windows Portable — AI Song Studio on Your Own PC

Full songs from lyrics, score editing, covers and voice conversion — on Windows,
offline after first setup, on NVIDIA GPUs from 12 GB VRAM. No Docker, no Linux, no conda.

[YouTube demo](#) • [Boosty — Extended edition](#) • [Hugging Face](#) • [Latest release](#) • [RU версия](README_ru.md)

## A personal note first
I'm saving up to bring my fiancée from the Philippines to my country — visa paperwork
and relocation cost more than I can earn quickly. So this project is my honest fundraiser:
the **Basic edition is free here, forever**, and the **Extended edition** (cover mode +
one-click RVC/Seed-VC voice conversion) funds the goal on Boosty. When the goal is reached,
everything that is on Boosty today goes public on these pages. No paywalled knowledge —
just a head start for those who want to help.

## What it is
A zero-config Windows packaging of YuE2 and friends that simply works:
- **Tab 1 — Text → Song:** lyrics + style prompt → complete song (vocals + instruments);
  confident singing in ru/en/zh/ja/ko/es.
- **Tab 2 — Score Editor:** rerender the ABC score with a new style, tempo or seed
  without regenerating the composition.
- **Tab 3 — Cover (Extended):** any MP3 → melody + lyrics transcription
  (SheetSage2 + faster-whisper) → cover in a new style.
- **Voice conversion (Extended):** RVC (trained voices) and Seed-VC (zero-shot from a
  10–30 s reference clip).
- **VRAM ladder:** auto tiling/chunking — 24 GB+ recommended, 16 GB supported,
  12 GB experimental.
- **Installer:** embedded Python 3.10, fully pinned freezes, portable ffmpeg,
  offline RVC base weights, resumable gated setup with logs.

## Editions
| | Basic — free (this repo) | Extended — Boosty |
|---|---|---|
| Text→Song + Score Editor | ✅ | ✅ |
| Cover mode (Tab 3) | — | ✅ |
| RVC + Seed-VC auto-installer | — | ✅ |
| Installer | `setup.bat` (lite) | `setup.bat` (full, VC menu) |

When the fiancée goal is reached, the Extended build is published here as a public release.

## Quick start
1. Download the Basic zip from Releases; verify SHA256.
2. Unpack anywhere (not Program Files), run `setup.bat` (Auto or Manual preset).
3. `verify_install.bat` → `start_webui.bat` → http://127.0.0.1:9099
4. First launch downloads YuE2 weights (~8 GB) from official Hugging Face repos
   under their original licenses.

## Requirements
- Windows 10/11 x64; NVIDIA GPU: 24 GB+ recommended / 16 GB supported / 12 GB experimental.
- ~40 GB free disk (Basic); internet for first-launch weights only.

## Under the hood
Embedded Python 3.10.11 · pinned `--no-deps` freezes · Windows SDPA patch for yue2 ·
huggingface-hub symlink-race patch · VRAM ladder with per-machine calibration ·
portable ffmpeg bundle · EN/RU UI · prompt helpers with structure tags.

## Upstream & licenses
This repository ships tooling and installers only — **no model weights**.
YuE2, SheetSage2, RVC (rvc-python), Seed-VC, demucs, faster-whisper and the ffmpeg builds
remain property of their authors; weights are downloaded from official repositories at first
launch under their original licenses (some are non-commercial). By using this tool you accept
upstream terms. My packaging code: MIT.

## Support
Boosty (Extended + updates) · YouTube demo · stars and shares move the fiancée goal directly.
Thank you.
