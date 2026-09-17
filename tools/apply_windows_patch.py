"""Apply the Windows SDPA patch to yue2/cuda_graph.py.

Windows PyTorch builds raise "USE_FLASH_ATTENTION was not enabled for build"
from the aten variable-length FlashAttention entrypoint, and SDPA backends are
not CUDA-Graph-capture-safe on Windows ("operation not permitted when stream is
capturing"). The patch disables CUDA Graphs entirely and runs decode eagerly
through the standard attention path (cuDNN / public SDPA).

Idempotent: if the target already contains the SDPA-WIN-PATCH marker, skip.
The pre-patch file is backed up once to <target>.orig.

Usage:
    python apply_windows_patch.py [TARGET] [--patch PATH]

TARGET is the cuda_graph.py file itself, or a site-packages directory that
contains yue2/cuda_graph.py. Default: python\Lib\site-packages\yue2\cuda_graph.py
(the main dist environment, relative to CWD).
"""
import argparse
import sys
from pathlib import Path

MARKER = "SDPA-WIN-PATCH"
MARKER_LINE = "# SDPA-WIN-PATCH: applied (Windows SDPA eager decode; CUDA Graphs disabled)"


def parse_hunks(patch_text):
    """Parse a unified diff into hunks: (old_start, old_lines, new_lines)."""
    hunks = []
    old_start = None
    old, new = [], []
    for line in patch_text.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        if line.startswith("@@"):
            if old_start is not None:
                hunks.append((old_start, old, new))
            old_start = int(line.split()[1][1:].split(",")[0])
            old, new = [], []
        elif line.startswith("+"):
            new.append(line[1:])
        elif line.startswith("-"):
            old.append(line[1:])
        elif line.startswith(" "):
            old.append(line[1:])
            new.append(line[1:])
    if old_start is not None:
        hunks.append((old_start, old, new))
    return hunks


def apply_hunks(source_lines, hunks):
    """Apply hunks in order. Raises ValueError when context does not match."""
    out = []
    pos = 0
    for old_start, old, new in hunks:
        start = old_start - 1
        if start < pos:
            raise ValueError(f"hunk overlaps previous hunk at line {start + 1}")
        out.extend(source_lines[pos:start])
        chunk = source_lines[start:start + len(old)]
        if chunk != old:
            detail = f"line {start + 1}: only {len(chunk)} of {len(old)} lines available"
            for i, (a, b) in enumerate(zip(chunk, old)):
                if a != b:
                    detail = f"line {start + i + 1}: got {a!r}, expected {b!r}"
                    break
            raise ValueError(f"context mismatch, {detail} -- is the file already patched?")
        out.extend(new)
        pos = start + len(old)
    out.extend(source_lines[pos:])
    return out


def main():
    ap = argparse.ArgumentParser(description="Apply the Windows SDPA patch to yue2/cuda_graph.py.")
    ap.add_argument("target", nargs="?", default=r"python\Lib\site-packages\yue2\cuda_graph.py",
                    help="cuda_graph.py path or site-packages dir (default: main dist env)")
    ap.add_argument("--patch", default=None,
                    help="windows_sdpa.patch path (default: next to this script)")
    args = ap.parse_args()

    target = Path(args.target)
    if target.is_dir():
        target = target / "yue2" / "cuda_graph.py"
    patch_path = (Path(args.patch) if args.patch
                  else Path(__file__).resolve().parent / "windows_sdpa.patch")
    if not target.is_file():
        print(f"[SDPA] ERROR: target not found: {target}")
        return 1
    if not patch_path.is_file():
        print(f"[SDPA] ERROR: patch not found: {patch_path}")
        return 1

    raw = target.read_bytes()
    text = raw.decode("utf-8")
    if MARKER in text:
        print(f"[SDPA] skip: {target} already contains the {MARKER} marker.")
        return 0

    hunks = parse_hunks(patch_path.read_text(encoding="utf-8"))
    eol = "\r\n" if text.count("\r\n") > text.count("\n") // 2 else "\n"
    lines = text.splitlines()
    try:
        patched = apply_hunks(lines, hunks)
    except ValueError as exc:
        print(f"[SDPA] ERROR: {exc}")
        return 1

    orig = Path(str(target) + ".orig")
    if not orig.is_file():
        orig.write_bytes(raw)
        print(f"[SDPA] backup: {orig}")

    out_text = eol.join(patched) + eol + MARKER_LINE + eol
    target.write_bytes(out_text.encode("utf-8"))
    print(f"[SDPA] applied: {target} ({len(lines)} -> {len(patched) + 1} lines, marker {MARKER})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
