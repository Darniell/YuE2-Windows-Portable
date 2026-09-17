"""Hardware preflight for the YuE2 LITE portable installer.

Only the main CUDA channel is checked.
"""
import ctypes
import datetime
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIST_ROOT = os.path.dirname(HERE)

CHANNEL_MIN_DRIVER = {"cu121": 531.0, "cu126": 560.0, "cu128": 571.0}
MIN_DISK_GB = 20.0
MIN_RAM_GB = 16.0


def gpu_info():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,compute_cap,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    parts = [p.strip() for p in out.stdout.strip().splitlines()[0].split(",")]
    if len(parts) < 4:
        return None
    info = {"name": parts[0], "driver": parts[3], "compute_cap": None, "vram_mib": None}
    try:
        info["compute_cap"] = float(parts[1])
    except ValueError:
        pass
    try:
        info["vram_mib"] = float(parts[2])
    except ValueError:
        pass
    return info


def ram_gb():
    try:
        st = ctypes.windll.kernel32.GlobalMemoryStatusEx
    except AttributeError:
        return None
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    stex = MEMORYSTATUSEX()
    stex.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not st(ctypes.byref(stex)):
        return None
    return stex.ullTotalPhys / (1024 ** 3)


def vram_class_gb(vram_gb):
    if vram_gb >= 24:
        return "recommended"
    if vram_gb >= 16:
        return "supported"
    if vram_gb >= 12:
        return "experimental"
    return "block"


def driver_ok(driver_str, channel):
    try:
        drv = float(driver_str)
    except (TypeError, ValueError):
        return False, "unknown"
    mn = CHANNEL_MIN_DRIVER[channel]
    return drv >= mn, "%.0f" % mn


def build_report(lines):
    with open(os.path.join(DIST_ROOT, "preflight_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_config(cfg):
    path = os.path.join(DIST_ROOT, "install_config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def check_common(blocks, warns, lines, gpu, ch_main):
    disk = shutil.disk_usage(DIST_ROOT)
    disk_gb = disk.free / (1024 ** 3)
    lines.append("Disk free (install drive): %.1f GB (required >= %.0f GB)" % (disk_gb, MIN_DISK_GB))
    if disk_gb < MIN_DISK_GB:
        blocks.append("free disk space %.1f GB < %.0f GB on the install drive" % (disk_gb, MIN_DISK_GB))

    ram = ram_gb()
    if ram is None:
        lines.append("RAM: unknown")
        warns.append("could not determine RAM size")
    else:
        lines.append("RAM: %.1f GB (required >= %.0f GB)" % (ram, MIN_RAM_GB))
        if ram < MIN_RAM_GB:
            warns.append("RAM %.1f GB < %.0f GB - install works but generation will be slow" % (ram, MIN_RAM_GB))

    if gpu is None:
        lines.append("Driver vs channel: nvidia-smi unavailable - cannot verify")
        blocks.append("NVIDIA driver not detected (nvidia-smi failed): CUDA builds of torch will not run")
    else:
        lines.append("Driver vs channel:")
        ok, mn = driver_ok(gpu["driver"], ch_main)
        lines.append("  main %s: %s (%s vs >= %s)" % (ch_main, "OK" if ok else "TOO OLD", gpu["driver"], mn))
        if not ok:
            blocks.append("driver %s is below the minimum %s for the main channel (%s)" % (gpu["driver"], mn, ch_main))


def main():
    mode = None
    if "--auto" in sys.argv:
        mode = "auto"
    elif "--verify-config" in sys.argv:
        mode = "verify-config"
    if mode is None:
        print(__doc__)
        return 2

    blocks, warns, lines = [], [], []
    lines.append("=== YuE2 LITE INSTALLER PREFLIGHT ===")
    lines.append("Date: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("Mode: " + mode)
    lines.append("")

    gpu = gpu_info()

    if mode == "auto":
        if gpu is None:
            lines.append("GPU: NOT DETECTED (nvidia-smi failed or not installed)")
            blocks.append("no NVIDIA GPU detected - CUDA builds of torch will not run")
        else:
            cc = gpu["compute_cap"]
            vram_gb = (gpu["vram_mib"] / 1024.0) if gpu["vram_mib"] else 0.0
            lines.append("GPU: %s" % gpu["name"])
            lines.append("Compute capability: %s" % (cc if cc else "?"))
            lines.append("VRAM: %.1f GB" % vram_gb)
            lines.append("Driver: %s" % gpu["driver"])

            ch_main = "cu128" if cc in (9.0, 10.0, 12.0) else "cu121"
            series = "50" if cc in (9.0, 10.0, 12.0) else "other" if cc and cc < min((8.6, 8.9)) else "40"
            cls = vram_class_gb(vram_gb)
            if cls == "block":
                blocks.append("VRAM %.1f GB < 12 GB - not supported by this release" % vram_gb)
            elif cls == "experimental":
                if os.environ.get("YUE2_ALLOW_12GB") == "1":
                    warns.append("VRAM %.1f GB is experimental (YUE2_ALLOW_12GB=1 acknowledged)" % vram_gb)
                else:
                    warns.append("VRAM %.1f GB is experimental: set YUE2_ALLOW_12GB=1 before setup.bat" % vram_gb)

            check_common(blocks, warns, lines, gpu, ch_main)
            lines.append("")
            lines.append("Verdict: " + ("BLOCK" if blocks else ("WARN" if warns else "READY")))
            lines.append("")
            if warns:
                lines.append("Warnings:")
                for w in warns:
                    lines.append("- " + w)
            if blocks:
                lines.append("Blockers:")
                for b in blocks:
                    lines.append("- " + b)
            lines.append("")
            lines.append("Full report: preflight_report.txt (this file)")
            cfg = {
                "mode": "auto",
                "series": series,
                "ch_main": ch_main,
                "vram_class": cls,
            }
            write_config(cfg)
            build_report(lines)
            print("\n".join(lines))
            if blocks:
                print("\nPREFLIGHT: BLOCK - install aborted. See preflight_report.txt")
                return 1
            print("\nPREFLIGHT: %s - continuing." % ("WARN" if warns else "READY"))
            return 0

    if mode == "verify-config":
        path = os.path.join(DIST_ROOT, "install_config.json")
        if not os.path.isfile(path):
            print("ERROR: install_config.json not found. Run setup.bat /manual first.")
            return 1
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        ch_main = str(cfg.get("ch_main") or "cu121").lower()
        if ch_main not in CHANNEL_MIN_DRIVER:
            blocks.append("unknown main channel %r" % ch_main)
        lines.append("Config: install_config.json (mode=%s, series=%s)" % (cfg.get("mode"), cfg.get("series")))
        lines.append("Main channel: %s" % ch_main)
        if gpu is None:
            lines.append("GPU: NOT DETECTED (nvidia-smi failed or not installed)")
            blocks.append("no NVIDIA GPU detected - CUDA builds of torch will not run")
        else:
            lines.append("GPU detected: %s (compute cap %s, driver %s, VRAM %s MiB)" % (
                gpu["name"], gpu["compute_cap"], gpu["driver"], gpu["vram_mib"]))
            check_common(blocks, warns, lines, gpu, ch_main)
        lines.append("")
        lines.append("Verdict: " + ("BLOCK" if blocks else ("WARN" if warns else "READY")))
        if warns:
            lines.append("Warnings:")
            for w in warns:
                lines.append("- " + w)
        if blocks:
            lines.append("Blockers:")
            for b in blocks:
                lines.append("- " + b)
        build_report(lines)
        print("\n".join(lines))
        if blocks:
            print("\nPREFLIGHT: BLOCK - install aborted. See preflight_report.txt")
            return 1
        print("\nPREFLIGHT: %s - continuing." % ("WARN" if warns else "READY"))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
