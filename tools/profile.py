"""Map install_config.json to torch pins used by setup.bat.

Usage:
    python tools/profile.py resolve          # KEY=VALUE for setup.bat
    python tools/profile.py print            # human-readable summary
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIST_ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(DIST_ROOT, "install_config.json")

CHANNEL_PINS = {
    "cu121": {"TORCH": "2.5.1+cu121", "TORCHAUDIO": "2.5.1+cu121", "TORCHVISION": "0.20.1+cu121"},
    "cu126": {"TORCH": "2.8.0+cu126", "TORCHAUDIO": "2.8.0+cu126", "TORCHVISION": "0.23.0+cu126"},
    "cu128": {"TORCH": "2.10.0+cu128", "TORCHAUDIO": "2.10.0+cu128", "TORCHVISION": "0.25.0+cu128"},
}


def load_config():
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def live_gpu_line():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,compute_cap,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return "GPU detected: nvidia-smi unavailable"
    if out.returncode != 0 or not out.stdout.strip():
        return "GPU detected: nvidia-smi unavailable"
    name, cc, mib, drv = [p.strip() for p in out.stdout.strip().splitlines()[0].split(",")]
    return "GPU detected: %s (compute cap %s, VRAM %s MiB, driver %s)" % (name, cc, mib, drv)


def resolve_pins(cfg):
    ch_main = str(cfg.get("ch_main") or "cu121").lower()
    if ch_main not in CHANNEL_PINS:
        return None, "unknown channel in install_config.json: %r" % ch_main
    m = CHANNEL_PINS[ch_main]
    pins = {
        "MAIN_TORCH": m["TORCH"],
        "MAIN_TORCHAUDIO": m["TORCHAUDIO"],
        "MAIN_TORCHVISION": m["TORCHVISION"],
        "MAIN_INDEX": ch_main,
        "PROFILE": "manual",
        "VRAM_CLASS": cfg.get("vram_class", "recommended"),
    }
    return pins, None


def main():
    if not os.path.isfile(CONFIG):
        print("ERROR: install_config.json not found (run setup.bat once, or setup.bat /manual).")
        return 1
    cfg = load_config()
    pins, err = resolve_pins(cfg)
    if err:
        print("ERROR: " + err)
        return 1

    if sys.argv[1:2] == ["resolve"]:
        for key in sorted(pins):
            print("%s=%s" % (key, pins[key]))
        return 0
    if sys.argv[1:2] == ["print"]:
        print("=== YuE2 LITE install profile ===")
        print("Date: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(live_gpu_line())
        print("Mode: %s (install_config.json)" % cfg.get("mode"))
        print("Series: %s" % cfg.get("series"))
        print("Channel: %s" % cfg.get("ch_main"))
        print("VRAM class: %s" % cfg.get("vram_class"))
        print("Torch pins:")
        print("  main: torch==%s torchaudio==%s torchvision==%s (index %s)" % (
            pins["MAIN_TORCH"], pins["MAIN_TORCHAUDIO"], pins["MAIN_TORCHVISION"], pins["MAIN_INDEX"]))
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
