"""Optional P2 (cu128) channel validation for the YuE2 portable installer.

Builds a scratch venv (.meta/p2_scratch) with torch cu128 (cp310-win) +
main freeze (--no-deps) + the yue2 wheel (--no-deps), applies the Windows
SDPA patch, and runs a 4-line smoke generation on the LOCAL GPU.

- Success: install_config.json channel_smoke = "channel smoke-tested on sm_XX"
  (XX = the local compute capability, e.g. sm_86 on RTX 30).
- Failure / prerequisites missing: "community verification pending".
In BOTH cases the P2 channel remains installable - this check never blocks.

Requirements: setup.bat has been run once (embedded python present) and the
live project hf_cache is next to install/ (offline model load).
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
DIST_ROOT = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(DIST_ROOT)
SCRATCH = os.path.join(DIST_ROOT, ".meta", "p2_scratch")
PY = os.path.join(DIST_ROOT, "python", "python.exe")
WHEEL = os.path.join(HERE, "yue2_infer-0.1.5-py3-none-any.whl")
FREEZE = os.path.join(DIST_ROOT, "dist_freeze", "requirements-main-freeze.txt")
REPORT = os.path.join(DIST_ROOT, "channel_smoke_report.txt")

PENDING = "community verification pending"


def set_smoke_status(status, lines):
    path = os.path.join(DIST_ROOT, "install_config.json")
    cfg = {}
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    cfg["channel_smoke"] = status
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("=== P2 (cu128) CHANNEL SMOKE ===\n")
        f.write("Date: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write("Status: " + status + "\n\n")
        f.write("\n".join(lines) + "\n")


def pip(sp, args, env, lines):
    r = subprocess.run([sp, "-m", "pip", "install", "--no-input"] + args, env=env)
    if r.returncode != 0:
        lines.append("pip install failed (rc=%s): %s" % (r.returncode, " ".join(args)))
    return r.returncode


def main():
    lines = []

    def finish(status):
        lines.append("Result: " + status)
        set_smoke_status(status, lines)
        shutil.rmtree(SCRATCH, ignore_errors=True)
        print("\n".join(lines))
        print("Report: " + REPORT)
        return 0

    lines.append("Scratch venv: " + SCRATCH)
    hf_home = os.path.join(REPO_ROOT, "hf_cache")
    if not os.path.isdir(hf_home):
        lines.append("Live hf_cache not found at %s - cannot run the offline smoke." % hf_home)
        return finish(PENDING)
    if os.path.isfile(PY):
        creator = [PY, "-m", "virtualenv"]
    else:
        # Embedded python not unpacked yet (setup.bat not run): fall back to any
        # local Python 3.10 with the virtualenv module, else py -3.10 stdlib venv.
        creator = None
        for cand in ([sys.executable, "-m", "virtualenv"],
                     ["py", "-3.10", "-m", "virtualenv"]):
            chk = subprocess.run(cand + ["--version"], capture_output=True, text=True)
            if chk.returncode == 0:
                creator = cand
                break
        if creator is None:
            chk = subprocess.run(["py", "-3.10", "-c", "import ensurepip"],
                                 capture_output=True)
            if chk.returncode == 0:
                creator = ["py", "-3.10", "-m", "venv"]
        if creator is None:
            lines.append("No venv creator available (run setup.bat first, or install virtualenv for py -3.10).")
            return finish(PENDING)

    env = dict(os.environ)
    env["PIP_CACHE_DIR"] = os.path.join(DIST_ROOT, "pip_cache")
    env["VIRTUALENV_APP_DATA"] = os.path.join(DIST_ROOT, ".meta", "virtualenv")
    env["TMP"] = os.path.join(DIST_ROOT, ".tmp")
    env["TEMP"] = env["TMP"]
    os.makedirs(env["TMP"], exist_ok=True)

    shutil.rmtree(SCRATCH, ignore_errors=True)
    print("[SMOKE] Creating scratch venv via: " + " ".join(creator))
    try:
        subprocess.check_call(creator + [SCRATCH], env=env)
        sp = os.path.join(SCRATCH, "Scripts", "python.exe")
        print("[SMOKE] Installing torch 2.10.0+cu128 (cp310-win)...")
        if pip(sp, ["torch==2.10.0+cu128", "torchaudio==2.10.0+cu128",
                    "--index-url", "https://download.pytorch.org/whl/cu128",
                    "--extra-index-url", "https://pypi.org/simple"], env, lines):
            return finish(PENDING)
        print("[SMOKE] Installing main freeze (--no-deps) + yue2 wheel (--no-deps)...")
        if pip(sp, ["--no-deps", "-r", FREEZE], env, lines):
            return finish(PENDING)
        if pip(sp, ["--no-deps", WHEEL], env, lines):
            return finish(PENDING)
        print("[SMOKE] Applying Windows SDPA patch to the scratch venv...")
        patch_runner = PY if os.path.isfile(PY) else sys.executable
        subprocess.check_call([patch_runner, os.path.join(HERE, "apply_windows_patch.py"),
                               os.path.join(SCRATCH, "Lib", "site-packages")], env=env)
    except Exception as exc:
        lines.append("Setup failed: %r" % exc)
        return finish(PENDING)

    smoke = r'''
import sys, os
sys.path.insert(0, os.environ["SMOKE_DIST_ROOT"])
import torch
major, minor = torch.cuda.get_device_capability(0)
print("[SMOKE] torch:", torch.__version__, "| device:", torch.cuda.get_device_name(0), "| cc:", major, minor)
assert torch.cuda.is_available()
import core.engine as engine
LYRICS = "[Verse]\nTest line one for the smoke check\nTest line two for the smoke check\n\n[Chorus]\nSmoke test chorus line\nSmoke test chorus line two\n"
r = engine.generate(LYRICS, "pop", cot="full", steps=16)
print("[SMOKE] ok:", r.get("ok"), "| audio:", r.get("audio_path"))
assert r.get("ok"), r
print("[SMOKE] PASSED")
'''
    env2 = dict(os.environ)
    env2["HF_HOME"] = hf_home
    env2["HF_HUB_CACHE"] = os.path.join(hf_home, "hub")
    env2["HF_HUB_OFFLINE"] = "1"
    env2["SMOKE_DIST_ROOT"] = DIST_ROOT
    print("[SMOKE] Running 4-line generation (offline, live hf_cache)...")
    try:
        out = subprocess.run([sp, "-c", smoke], env=env2, cwd=DIST_ROOT,
                             capture_output=True, text=True, timeout=3600)
        lines.append(out.stdout.strip())
        if out.returncode != 0 or "[SMOKE] PASSED" not in out.stdout:
            lines.append("Smoke failed (rc=%s)." % out.returncode)
            lines.append((out.stderr or "")[-2000:])
            cc = "?"
            for ln in out.stdout.splitlines():
                if ln.startswith("[SMOKE] torch:"):
                    cc = ln.split("cc:")[1].strip().replace(" ", "")
            return finish(PENDING if cc == "?" else
                          "community verification pending (local smoke failed on sm_%s)" % cc)
        cc = ""
        for ln in out.stdout.splitlines():
            if ln.startswith("[SMOKE] torch:"):
                cc = ln.split("cc:")[1].strip().replace(" ", "")
        return finish("channel smoke-tested on sm_%s" % cc)
    except Exception:
        lines.append("Smoke crashed:")
        lines.append(traceback.format_exc()[-2000:])
        return finish(PENDING)


if __name__ == "__main__":
    sys.exit(main())
