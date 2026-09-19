"""Обертка над YuE2Pipeline: загрузка модели один раз, потокобезопасная генерация."""
import dataclasses
import gc
import os
import re
import shutil
import threading
import time
from pathlib import Path

import torch
import torch.nn.functional as F

# === СИСТЕМНЫЙ ПАТЧ WINDOWS (SDPA вместо Flash Attention) ===
if not hasattr(torch.ops.aten, "_flash_attention_forward"):
    def _windows_flash_attention_forward(query, key, value, *args, **kwargs):
        if query.dim() == 4:
            q = query.transpose(1, 2)
            k = key.transpose(1, 2)
            v = value.transpose(1, 2)
        elif query.dim() == 3:
            q = query.unsqueeze(1)
            k = key.unsqueeze(1)
            v = value.unsqueeze(1)
        else:
            q, k, v = query, key, value
        with torch.backends.cuda.sdp_kernel(enable_flash=False, enable_math=True,
                                            enable_mem_efficient=True):
            out = F.scaled_dot_product_attention(q, k, v)
        if query.dim() == 4:
            out = out.transpose(1, 2)
        elif query.dim() == 3:
            out = out.squeeze(1)
        e = torch.empty(0, device=query.device)
        return (out, query, key, value, e, e, e)

    torch.ops.aten._flash_attention_forward = _windows_flash_attention_forward
# ============================================================

from yue2 import YuE2Pipeline, SongResult, SymbolicPlan, SemanticResult  # noqa: E402

os.environ.setdefault("HF_HOME", r"L:\ai\audio\YuE2\hf_cache")

# Локализация пользовательских строк (ошибки/гейт); язык переключает app.
from core.i18n import t  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Глобальный VRAM Lock: защищает от параллельного доступа к модели (OOM).
GENERATION_LOCK = threading.Lock()

# Дефолтный seed пайплайна YuE2 (SongRequest.seed), задаем явно для воспроизводимости.
DEFAULT_SEED = 831001

# Штатные значения ODE-шагов NAR-синтеза (GenerationConfig.ode_steps, protocol.py:48;
# валидация int >= 1, nar.py:178-179). 32 — дефолт релиза ("Best"), 16 — "Fast".
ODE_STEPS_FAST = 16
ODE_STEPS_BEST = 32

_pipe = None
_INIT_LOCK = threading.Lock()


def clear_vram():
    """Принудительное освобождение VRAM: кэш CUDA-аллокатора + сборка мусора."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def vram_info():
    """Строка-индикатор занятой VRAM: 'VRAM: X.X GB / 24 GB'."""
    if not torch.cuda.is_available():
        return t("vram_no_cuda")
    free, total = torch.cuda.mem_get_info()
    return f"VRAM: {(total - free) / 2**30:.1f} / {total / 2**30:.1f} GB"


def _apply_vram_limit():
    """YUE2_VRAM_LIMIT_GB: эмуляция слабой карты — cap аллокатора torch.

    set_per_process_memory_fraction(limit/total) ДО загрузки модели: попытки
    выделения сверх лимита дают torch.cuda.OutOfMemoryError, лестница чанкования
    отрабатывает штатно. Переменная не задана -> поведение по умолчанию.
    """
    raw = os.environ.get("YUE2_VRAM_LIMIT_GB", "").strip()
    if not raw or not torch.cuda.is_available():
        return
    try:
        limit_gb = float(raw)
    except ValueError:
        print(f"[VRAM] limit: нечисловое значение '{raw}' — игнорируется", flush=True)
        return
    if limit_gb <= 0:
        return
    total_gb = torch.cuda.get_device_properties(0).total_memory / 2**30
    torch.cuda.set_per_process_memory_fraction(min(limit_gb / total_gb, 1.0), 0)
    print(f"[VRAM] limit: {limit_gb:g} GB (карта {total_gb:.1f} GB)", flush=True)


def get_pipeline():
    """Ленивый singleton: модель грузится в VRAM строго один раз за процесс."""
    global _pipe
    if _pipe is None:
        with _INIT_LOCK:
            if _pipe is None:
                _apply_vram_limit()
                _pipe = YuE2Pipeline.from_pretrained("m-a-p/YuE2-3B", device="cuda")
    return _pipe


def is_busy():
    return GENERATION_LOCK.locked()


def _apply_ode_steps(pipe, steps):
    """Штатная ручка качества рендера: GenerationConfig.ode_steps.

    pipe.synthesize (pipeline.py:301) и _synthesize_direct читают
    pipe.generation_config.ode_steps; GenerationConfig frozen — заменяем
    через dataclasses.replace. Валидация int >= 1 в GenerationConfig.__post_init__.
    """
    used = ODE_STEPS_BEST if steps is None else int(steps)
    if used != pipe.generation_config.ode_steps:
        pipe.generation_config = dataclasses.replace(pipe.generation_config, ode_steps=used)
    return used


# Последняя VRAM-метка этапа (для Status в UI).
_LAST_STAGE = ""


def last_stage():
    """Последняя метка этапа с VRAM: '[VRAM] after semantic | VRAM: X.X / 24.0 GB'."""
    return _LAST_STAGE


def _mark(label):
    """Пишет метку этапа + текущую VRAM в консоль и запоминает для UI."""
    global _LAST_STAGE
    _LAST_STAGE = f"{label} | {vram_info()}"
    print(f"[VRAM] {_LAST_STAGE}", flush=True)


def _free_gb():
    if not torch.cuda.is_available():
        return float("inf")
    free, _ = torch.cuda.mem_get_info()
    return free / 2**30


def _own_used_gb():
    """VRAM, зарезервированная этим процессом (базовые веса + фрагментация)."""
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.memory_reserved() / 2**30


# Длительность/токены последней генерации (для Status в UI и VRAM-гейта).
_LAST_DURATION_SEC = 0.0
_LAST_TOKENS = 0


def last_duration_sec():
    """Длительность последней генерации, сек (после semantic — точная: tokens/25)."""
    return _LAST_DURATION_SEC


def last_tokens():
    """Число semantic-токенов последней генерации."""
    return _LAST_TOKENS


def _estimate_duration_sec(abc):
    """Грубая оценка длительности по ABC: Q: (BPM), M: (метр), число тактов '|'."""
    if not abc:
        return 0.0
    bpm, num, den = 120.0, 4.0, 4.0
    bars_per_voice = {}
    voice = ""
    for raw in abc.splitlines():
        line = raw.strip()
        if not line or line[:2] in ("w:", "W:"):
            continue
        head = line[:2]
        if head == "Q:":
            m = re.search(r"=\s*([0-9.]+)", line)
            if not m:
                m = re.search(r"([0-9.]+)\s*$", line)
            if m:
                try:
                    bpm = float(m.group(1))
                except ValueError:
                    pass
        elif head == "M:":
            body = line[2:].strip()
            if body in ("C", "c"):
                num, den = 4.0, 4.0
            elif body in ("C|", "c|"):
                num, den = 2.0, 2.0
            else:
                m = re.match(r"(\d+)\s*/\s*(\d+)", body)
                if m:
                    num, den = float(m.group(1)), float(m.group(2))
        elif head == "V:":
            voice = line[2:].strip()
        elif re.match(r"^[A-Za-z]:", line):
            continue  # заголовки X:, T:, K:, L: и т.п.
        else:
            bars_per_voice[voice] = bars_per_voice.get(voice, 0) + line.count("|")
    bars = max(bars_per_voice.values()) if bars_per_voice else 0
    if bars <= 0 or bpm <= 0:
        return 0.0
    sec_per_bar = num * (4.0 / den) * 60.0 / bpm
    return bars * sec_per_bar


# VRAM-модель синтеза: база 8.1 GB поверх модели (замеры VRAM_FIX_v2/v3).
# Пики измеряются напрямую ([PEAK]) и накапливаются в calibration.json;
# пока на режим < 2 замеров — константы v3 (рост ≈ 0.6 + 2.47 GB/мин,
# offload_ar -2.5) и маржа 1.5 GB; после 2 замеров — пик + маржа 1.0 GB.
_SYNTH_BASE_GB = 8.1
_SYNTH_INTERCEPT_GB = 0.6
_SYNTH_MEASURED_GB_PER_MIN = 2.47
_SYNTH_OFFLOAD_DISCOUNT_GB = 2.5
_FALLBACK_MARGIN_GB = 1.5          # маржа, пока < 2 пик-замеров на режим
_READY_MARGIN_GB = 1.0             # маржа при >= 2 замерах
_QUERY_CHUNK = 256
_MIN_CHUNK_TOKENS = 600            # 24 c — минимальный осмысленный чанк
_SAFE_CHUNK_TOKENS = 1500          # 1.0 мин — гарантированный чанк финальной попытки
_TOKENS_PER_MIN = 1500             # 25 ток./с * 60 c (ИСПРАВЛЕНО: было *25 -> 88 ток.)
_CALIB_PATH = PROJECT_ROOT / "calibration.json"

_PEAK_SAMPLES = {"single": [], "tiling": [], "chunked": []}


def _load_calibration():
    import json
    if _CALIB_PATH.is_file():
        try:
            data = json.loads(_CALIB_PATH.read_text(encoding="utf-8"))
            for mode in _PEAK_SAMPLES:
                _PEAK_SAMPLES[mode] = [tuple(s) for s in data.get(mode, [])]
        except Exception:
            pass


def _save_calibration():
    import json
    try:
        _CALIB_PATH.write_text(json.dumps(
            {m: [list(s) for s in v] for m, v in _PEAK_SAMPLES.items()}, indent=1),
            encoding="utf-8")
    except Exception:
        pass


def _record_peak(mode, minutes, peak_gb):
    """minutes — длительность аудио в вызове (для chunked — на один чанк)."""
    if not any(abs(s[0] - minutes) < 1e-3 and abs(s[1] - peak_gb) < 0.05
               for s in _PEAK_SAMPLES[mode]):
        _PEAK_SAMPLES[mode].append((round(minutes, 3), round(peak_gb, 2)))
        _save_calibration()


def _mode_ready(mode):
    return len(_PEAK_SAMPLES[mode]) >= 2


def _mode_slope_gb_per_min(mode):
    """Наклон роста пика по накопленным замерам (fallback — константа v3)."""
    pts = sorted(_PEAK_SAMPLES[mode])
    if len(pts) >= 2 and pts[-1][0] > pts[0][0]:
        return max(0.2, (pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0]))
    return _SYNTH_MEASURED_GB_PER_MIN


def _required_gb(minutes):
    """Требуемая VRAM для single: пик из >= 2 замеров; иначе формула v3 + маржа 1.5."""
    if _mode_ready("single"):
        return max(p for _, p in _PEAK_SAMPLES["single"]) + _READY_MARGIN_GB
    return (_SYNTH_BASE_GB + _SYNTH_INTERCEPT_GB
            + _SYNTH_MEASURED_GB_PER_MIN * minutes
            - _SYNTH_OFFLOAD_DISCOUNT_GB + _FALLBACK_MARGIN_GB)


def _measured_required_gb(minutes):
    """Требуемая VRAM для tiling (один чанк + тайлинг + offload AR)."""
    if _mode_ready("tiling"):
        return max(p for _, p in _PEAK_SAMPLES["tiling"]) + _READY_MARGIN_GB
    return (_SYNTH_BASE_GB + _SYNTH_INTERCEPT_GB
            + _SYNTH_MEASURED_GB_PER_MIN * minutes
            - _SYNTH_OFFLOAD_DISCOUNT_GB + _FALLBACK_MARGIN_GB)


def _chunk_budget_tokens(free, own_used):
    """Бюджет токенов на чанк из доступной VRAM (avail = free + own_used).

    Наклон: (required - own_used) / tokens_total — прирост VRAM на токен сверх базы.
    budget_tokens = free / наклон — сколько токенов помещается в свободную VRAM.
    """
    slope_per_min = _mode_slope_gb_per_min("chunked")
    margin = _READY_MARGIN_GB if _mode_ready("chunked") else _FALLBACK_MARGIN_GB
    # required = base + intercept + slope*min - offload + margin
    # own_used ≈ base (веса модели); delta = required - own_used = рост синтеза
    req_1min = (_SYNTH_BASE_GB + _SYNTH_INTERCEPT_GB
                + slope_per_min * 1.0
                - _SYNTH_OFFLOAD_DISCOUNT_GB + margin)
    delta_per_min = max(0.1, req_1min - own_used)
    slope_per_token = delta_per_min / _TOKENS_PER_MIN
    if slope_per_token <= 0:
        return int(1e9)  # нет роста -> без ограничений
    budget = int(free / slope_per_token)
    return budget


def _chunk_gate_avail_gb(own_used):
    """Порог гейта на маргинальной базе: own_used + slope*min_tokens <= avail.

    Гарантирует, что минимальный осмысленный чанк (_MIN_CHUNK_TOKENS) поместится
    в доступную VRAM (avail = free + own_used).
    """
    slope_per_min = _mode_slope_gb_per_min("chunked")
    margin = _READY_MARGIN_GB if _mode_ready("chunked") else _FALLBACK_MARGIN_GB
    min_minutes = _MIN_CHUNK_TOKENS / _TOKENS_PER_MIN
    req = (_SYNTH_BASE_GB + _SYNTH_INTERCEPT_GB
           + slope_per_min * min_minutes
           - _SYNTH_OFFLOAD_DISCOUNT_GB + margin)
    return req  # avail >= req => чанк гарантирован


def _gate_error(minutes, free, reason=""):
    return t("gate_error", min=f"{minutes:.1f}", tokens=_LAST_TOKENS,
             free=f"{free:.1f}", reason=reason)


_load_calibration()


def _ladder(minutes, free, n_tokens, prefix_len, own_used):
    """Решение лестницы синтеза. avail = free + own_used (исключает double-count весов).

    Returns (decision, context, reason).
    """
    required = _required_gb(minutes)
    measured = _measured_required_gb(minutes)
    avail = free + own_used

    def chunk_ctx(tokens_per_chunk):
        return min(24576, 2 * tokens_per_chunk + prefix_len + 3)

    if required <= avail:
        decision, context = "single", None
        reason = (f"required {required:.1f} <= avail {avail:.1f} "
                  f"(free={free:.1f} own_used={own_used:.1f}, "
                  f"{'peak-calibrated' if _mode_ready('single') else 'formula+margin1.5'})")
    elif measured <= avail:
        decision, context = "tiling", 24576
        reason = (f"required {required:.1f} > avail {avail:.1f}, "
                  f"measured {measured:.1f} <= avail (tiling+offload, "
                  f"free={free:.1f} own_used={own_used:.1f})")
    else:
        chunk_tokens = min(_chunk_budget_tokens(free, own_used), n_tokens)
        if chunk_tokens < _MIN_CHUNK_TOKENS:
            decision, context = "error", None
            reason = (f"бюджет чанка {chunk_tokens} ток. < минимума {_MIN_CHUNK_TOKENS}; "
                      f"avail {avail:.1f} (free={free:.1f} own_used={own_used:.1f}) "
                      f"< required {required:.1f} и < measured {measured:.1f}")
        else:
            decision, context = "chunked", chunk_ctx(chunk_tokens)
            n_chunks = (n_tokens + chunk_tokens - 1) // chunk_tokens
            reason = (f"avail {avail:.1f} (free={free:.1f} own_used={own_used:.1f}) "
                      f"< measured {measured:.1f}; "
                      f"чанк {chunk_tokens} ток. (~{chunk_tokens / _TOKENS_PER_MIN:.1f} мин), "
                      f"{n_chunks} чанков")
    print(f"[LADDER] free={free:.1f} own_used={own_used:.1f} avail={avail:.1f} "
          f"required={required:.1f} measured={measured:.1f} "
          f"chunk_min_tokens={_MIN_CHUNK_TOKENS} decision={decision} reason={reason}",
          flush=True)
    return decision, context, reason


def _synthesize_direct(pipe, semantic, context):
    """Обёртка над yue2.nar.synthesize: свой context (чанки) + query_chunk_size.

    Дублирует вызов pipeline.synthesize (валидация префикса уже пройдена в
    generate_semantic), yue2/ не изменяется.
    """
    from yue2 import nar as yue2_nar
    if pipe.quantization != "none":
        from yue2.quantization import restore_ar
        restore_ar(pipe._model)
    model = pipe._load_model(for_nar=True)
    with pipe._status("Synthesizing audio", unit="steps") as status:
        report = (lambda completed, total: status.update(completed, total=total)) if pipe.progress else None
        result = yue2_nar.synthesize(model, semantic.plan.prefix, semantic.tokens,
                                     semantic.plan.request.seed,
                                     steps=pipe.generation_config.ode_steps,
                                     context=context, offload_ar=pipe.offload_ar,
                                     query_chunk_size=_QUERY_CHUNK,
                                     on_progress=report)
        return result.detach().float().cpu().numpy()


def _synthesize(pipe, semantic, minutes, free, own_used):
    """Этап synthesize: лестница single -> tiling -> chunked с peak-замерами
    ([PEAK]) и ступенчатым retry при OOM (следующая ступень, максимум 2 retry).

    P2: pipe.offload_ar=True — AR-модули модели уходят на CPU на время ODE.
    P3: при нехватке VRAM — обёртка над yue2.nar.synthesize с уменьшенным
    context (чанки) + query_chunk_size (тайлинг внимания).
    """
    n_tokens = len(semantic.tokens)
    prefix_len = len(semantic.plan.prefix)
    prev_offload = pipe.offload_ar
    pipe.offload_ar = True
    try:
        decision, context, reason = _ladder(minutes, free, n_tokens, prefix_len, own_used)
        attempts = []
        if decision == "single":
            attempts.append(("single", None))
        elif decision == "tiling":
            attempts.append(("tiling", 24576))
        elif decision == "chunked":
            attempts.append(("chunked", context))
        else:
            # Гейт: при достаточном avail чанкование ОБЯЗАНО быть попытано.
            gate_threshold = _chunk_gate_avail_gb(own_used)
            avail = free + own_used
            if avail >= gate_threshold:
                context = min(24576, 2 * _SAFE_CHUNK_TOKENS + prefix_len + 3)
                decision = "chunked"
                attempts.append(("chunked", context))
                print(f"[GATE] avail {avail:.1f} (free={free:.1f} own_used={own_used:.1f}) "
                      f">= {gate_threshold:.1f} -> force chunked 1.0 мин", flush=True)
            else:
                raise RuntimeError(_gate_error(minutes, free, reason))
        # Ступени retry: single/tiling -> 2 чанка -> 4 чанка (максимум 2 retry).
        for n_chunks in (2, 4):
            ctx = min(24576, 2 * -(-n_tokens // n_chunks) + prefix_len + 3)
            if all(ctx != c for _, c in attempts):
                attempts.append(("chunked", ctx))
        attempts = attempts[:3]

        last_error = None
        for attempt_no, (mode, ctx) in enumerate(attempts, 1):
            try:
                if torch.cuda.is_available():
                    torch.cuda.reset_peak_memory_stats()
                t0 = time.perf_counter()
                if mode == "single":
                    out = pipe.synthesize(semantic)
                else:
                    print(f"[VRAM] synthesize: {mode}, context={ctx}", flush=True)
                    out = _synthesize_direct(pipe, semantic, ctx)
                peak = (torch.cuda.max_memory_allocated() / 2**30
                        if torch.cuda.is_available() else 0.0)
                call_min = (minutes if mode != "chunked"
                            else max(0.1, ((ctx - prefix_len - 3) // 2) / _TOKENS_PER_MIN))
                _record_peak(mode, call_min, peak)
                print(f"[PEAK] synthesize: {peak:.1f} GB (mode={mode}, context={ctx}, "
                      f"{time.perf_counter() - t0:.0f} c, "
                      f"samples={len(_PEAK_SAMPLES[mode])})", flush=True)
                return out
            except torch.cuda.OutOfMemoryError as exc:
                last_error = exc
                print(f"[LADDER] OOM на попытке {attempt_no}/{len(attempts)} "
                      f"(mode={mode}, context={ctx}): {exc}", flush=True)
                clear_vram()
        raise RuntimeError(_gate_error(
            minutes, free,
            f"OOM на всех {len(attempts)} ступенях лестницы "
            f"({', '.join(m for m, _ in attempts)}); последняя ошибка: {last_error}"))
    finally:
        pipe.offload_ar = prev_offload


def _run_song(pipe, request, session_dir):
    """Пошаговый прогон пайплайна: после каждого этапа — "extract minimal
    payload, then del" + clear_vram(), чтобы KV-кэш и пиковые выделения этапа
    не жили до синтеза. Перед synthesize — VRAM-гейт с понятной ошибкой.
    """
    from yue2.storage import identity

    global _LAST_DURATION_SEC, _LAST_TOKENS

    config = pipe.effective_config(request)
    request_id = identity({"request": request.to_dict(), "config": config, "weights": pipe.weights})
    start = time.perf_counter()

    # --- Этап 1: plan ---
    _mark("[VRAM] before plan")
    plan = pipe.plan(request=request)
    plan_payload = (plan.abc, list(plan.abc_ids), list(plan.prefix),
                    dict(plan.timing), plan.truncated)
    del plan
    clear_vram()
    _mark("[VRAM] after plan")
    plan = SymbolicPlan(request, plan_payload[0], plan_payload[1],
                        plan_payload[2], plan_payload[3], plan_payload[4])
    del plan_payload

    # --- Оценка длительности по ABC ---
    _LAST_DURATION_SEC = _estimate_duration_sec(plan.abc)
    print(f"[DUR] estimate: {_LAST_DURATION_SEC / 60:.1f} min", flush=True)

    # --- Этап 2: semantic ---
    _mark("[VRAM] before semantic")
    semantic = pipe.generate_semantic(plan)
    semantic_payload = (list(semantic.tokens), dict(semantic.timing), semantic.truncated)
    del semantic
    clear_vram()
    _mark("[VRAM] after semantic")
    semantic = SemanticResult(plan, semantic_payload[0], semantic_payload[1], semantic_payload[2])
    del semantic_payload

    # --- Точная длительность: tokens / 25 Hz ---
    _LAST_TOKENS = len(semantic.tokens)
    _LAST_DURATION_SEC = _LAST_TOKENS / 25.0
    print(f"[DUR] exact: {_LAST_DURATION_SEC / 60:.1f} min", flush=True)

    # --- VRAM-гейт перед синтезом ---
    minutes = _LAST_DURATION_SEC / 60.0
    free = _free_gb()
    own_used = _own_used_gb()
    avail = free + own_used
    if free < 6.0:
        raise RuntimeError(t("gate_vram", free=f"{free:.1f}"))
    gate_threshold = _chunk_gate_avail_gb(own_used)
    if avail < gate_threshold:
        print(f"[GATE] avail {avail:.1f} GB (free={free:.1f} own_used={own_used:.1f}) "
              f"< порога гарантированного чанка {gate_threshold:.1f} GB — "
              f"чанкование ограничено бюджетом", flush=True)
    _mark("[VRAM] before synthesize")

    # --- Этап 3: synthesize (P2: offload AR, P3: авто-чанкование) ---
    nar_start = time.perf_counter()
    latents = _synthesize(pipe, semantic, minutes, free, own_used)
    nar_seconds = time.perf_counter() - nar_start
    _mark("[VRAM] after synthesize")

    # --- Этап 4: decode ---
    vae_start = time.perf_counter()
    audio = pipe.decode(latents)
    timing = {"abc": plan.timing, "semantic": semantic.timing, "nar_seconds": nar_seconds,
              "vae_seconds": time.perf_counter() - vae_start, "load": dict(pipe.load_timing),
              "e2e_seconds": time.perf_counter() - start}
    song = SongResult(audio, 48000, semantic, latents, config, pipe.weights, timing, request_id)
    song.save_artifacts(session_dir)
    del latents
    clear_vram()
    _mark("[VRAM] after decode")
    return song


def generate(lyrics, style, cot="full", seed=None, steps=None):
    """Генерация трека. Захватывает GENERATION_LOCK без ожидания.

    cot: "full" (по умолчанию), "melody" или "off" ("No score" — штатная ветка
    plan() без генерации партитуры, pipeline.py:258-259).
    seed: None -> DEFAULT_SEED (обратная совместимость), иначе переданное значение.
    steps: None -> ODE_STEPS_BEST (32), иначе число ODE-шагов (напр. 16 = "Fast").
    Returns dict: {ok, error, audio_path, abc, session_dir, seed, steps, cot}.
    """
    used_seed = DEFAULT_SEED if seed is None else int(seed)
    used_steps = ODE_STEPS_BEST if steps is None else int(steps)
    result = {"ok": False, "error": "", "audio_path": "", "abc": "", "session_dir": "",
              "seed": used_seed, "steps": used_steps, "cot": cot}
    if not GENERATION_LOCK.acquire(blocking=False):
        result["error"] = t("err_busy")
        return result
    try:
        pipe = get_pipeline()
        result["steps"] = _apply_ode_steps(pipe, used_steps)
        session_dir = OUTPUTS_DIR / f"web_ui_{time.strftime('%Y%m%d_%H%M%S')}"
        request = pipe._request(style, lyrics, cot=cot, seed=used_seed)
        song = _run_song(pipe, request, session_dir)
        result.update(ok=True,
                      audio_path=str(session_dir / "audio.flac"),
                      abc=song.abc,
                      session_dir=str(session_dir))
        return result
    except Exception as exc:
        result["error"] = t("err_generation", err=exc)
        return result
    finally:
        clear_vram()
        GENERATION_LOCK.release()


def render_from_abc(abc_code, style, lyrics, seed=None, cot="full", steps=None,
                    cfg_scale=None):
    """Рендер аудио из готового ABC-кода.

    Обход LLM-этапа plan(): ABC инжектится в SongRequest (request.abc), и
    plan() берет ветку "Using provided score" без генерации партитуры.
    cot: "full" (по умолчанию) или "melody" (внешний ABC требует melody/full
    по протоколу yue2, protocol.py:99-100; "off" запрещен — гвард ниже).
    steps: None -> ODE_STEPS_BEST (32), иначе число ODE-шагов (16 = "Fast").
    cfg_scale: None -> штатный дефолт yue2 (параметр не передается), иначе
    guidance/cfg_scale (валидация protocol.py:101-106, диапазон 0-20).
    Возвращает dict: {ok, error, audio_path, abc, session_dir, seed, steps, cot}.
    """
    used_steps = ODE_STEPS_BEST if steps is None else int(steps)
    result = {"ok": False, "error": "", "audio_path": "", "abc": "", "session_dir": "",
              "seed": seed if seed is not None else DEFAULT_SEED,
              "steps": used_steps, "cot": cot}
    if not (abc_code or "").strip():
        result["error"] = t("err_empty_score")
        return result
    if cot == "off":
        result["error"] = t("err_cot_off_ext")
        return result
    if not (style or "").strip() or not (lyrics or "").strip():
        result["error"] = t("err_unknown_ctx")
        return result
    if not GENERATION_LOCK.acquire(blocking=False):
        result["error"] = t("err_busy")
        return result
    try:
        pipe = get_pipeline()
        result["steps"] = _apply_ode_steps(pipe, used_steps)
        session_dir = OUTPUTS_DIR / f"web_ui_{time.strftime('%Y%m%d_%H%M%S')}"
        if cfg_scale is None:
            request = pipe._request(style, lyrics, cot=cot,
                                    seed=result["seed"], abc=abc_code)
        else:
            request = pipe._request(style, lyrics, cot=cot,
                                    seed=result["seed"], abc=abc_code,
                                    cfg_scale=float(cfg_scale))
        song = _run_song(pipe, request, session_dir)
        result.update(ok=True,
                      audio_path=str(session_dir / "audio.flac"),
                      abc=song.abc,
                      session_dir=str(session_dir))
        return result
    except Exception as exc:
        result["error"] = t("err_render", err=exc)
        return result
    finally:
        clear_vram()
        GENERATION_LOCK.release()


def generate_with_reference(audio_path, lyrics, style, strength=3.0, steps=None):
    """Cover-генерация на основе референсного аудио.

    YuE2Pipeline не принимает аудио-вход (параметров audio_prompt / reference_track
    в API нет), поэтому влияние референса реализовано штатными средствами:
    - референс копируется в артефакты сессии (reference.*);
    - сила влияния = cfg_scale (guidance): насколько строго модель следует
      текстовому описанию стиля референса (1.0 — свободно, выше — строже; API: 0-20).
    steps: None -> ODE_STEPS_BEST (32), иначе число ODE-шагов (16 = "Fast").
    Returns dict: {ok, error, audio_path, abc, session_dir, seed, steps, cot, reference_path}.
    """
    used_steps = ODE_STEPS_BEST if steps is None else int(steps)
    result = {"ok": False, "error": "", "audio_path": "", "abc": "", "session_dir": "",
              "seed": DEFAULT_SEED, "steps": used_steps, "cot": "full", "reference_path": ""}
    if not (lyrics or "").strip():
        result["error"] = t("err_no_lyrics")
        return result
    if not (style or "").strip():
        result["error"] = t("err_no_ref_style")
        return result
    if not audio_path:
        result["error"] = t("err_no_ref")
        return result
    ref = Path(audio_path)
    if not ref.is_file():
        result["error"] = t("err_ref_missing", path=ref)
        return result
    if not GENERATION_LOCK.acquire(blocking=False):
        result["error"] = t("err_busy")
        return result
    try:
        pipe = get_pipeline()
        result["steps"] = _apply_ode_steps(pipe, used_steps)
        session_dir = OUTPUTS_DIR / f"web_ui_{time.strftime('%Y%m%d_%H%M%S')}"
        session_dir.mkdir(parents=True, exist_ok=True)
        reference_path = session_dir / f"reference{ref.suffix.lower()}"
        shutil.copyfile(ref, reference_path)
        request = pipe._request(style, lyrics, cot="full",
                                seed=DEFAULT_SEED, cfg_scale=float(strength))
        song = _run_song(pipe, request, session_dir)
        result.update(ok=True,
                      audio_path=str(session_dir / "audio.flac"),
                      abc=song.abc,
                      session_dir=str(session_dir),
                      reference_path=str(reference_path))
        return result
    except Exception as exc:
        result["error"] = t("err_cover_gen", err=exc)
        return result
    finally:
        clear_vram()
        GENERATION_LOCK.release()
