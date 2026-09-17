# [DIST_PATCH] huggingface_hub 0.36.2 (pinned by yue2-infer): are_symlinks_supported
# stores a provisional True for the cache dir BEFORE the real support test completes.
# Parallel first-run downloads (snapshot_download, 8 workers) on Windows without
# symlink privileges (no Developer Mode / not admin) can read the provisional True
# and race-crash at os.symlink (WinError 1314: "A required privilege is not held").
# Initializing with False is always safe:
#   - unprivileged machines: copy/move fallback (standard no-symlink cache mode);
#   - privileged machines: symlinks after the first per-dir test completes.
# Idempotent: skips files already marked with [DIST_PATCH].
import sys
from pathlib import Path

TARGET = "huggingface_hub/file_download.py"
OLD = "        _are_symlinks_supported_in_dir[cache_dir] = True"
NEW = ("        _are_symlinks_supported_in_dir[cache_dir] = False  "
       "# [DIST_PATCH] no provisional True: parallel first-run downloads on "
       "Windows without symlink privileges otherwise race-crash at os.symlink")

for sp in sys.argv[1:]:
    p = Path(sp) / TARGET
    if not p.is_file():
        print(f"[DIST_PATCH] {p} not found, skipped")
        continue
    s = p.read_text(encoding="utf-8")
    if "[DIST_PATCH]" in s:
        print(f"[DIST_PATCH] {p} already patched")
        continue
    assert OLD in s, f"pattern not found in {p}"
    p.write_text(s.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"[DIST_PATCH] {p} patched")
