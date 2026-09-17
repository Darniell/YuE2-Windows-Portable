"""YuE2 Web UI. Lite edition: Text2Music + Score Editor. Server: 127.0.0.1:9099."""
import json
import os
import random
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
os.environ["HF_HOME"] = str(BASE / "hf_cache")
os.environ.setdefault("HF_HUB_CACHE", str(BASE / "hf_cache" / "hub"))
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import gradio as gr

from core import abc_tools, engine, i18n, presets, state

# Choices maps contain labels in both languages so the dropdown value stays valid
# after language switches.
_COT_KEYS = (("full", "cot_full"), ("melody", "cot_melody"), ("off", "cot_off"))
_STEPS_KEYS = (("fast", "steps_fast"), ("best", "steps_best"))


def _label_map(keys):
    m = {}
    for code, key in keys:
        for lg in ("en", "ru"):
            m[i18n.t(key, lg)] = code
    return m


_COT_MAP = _label_map(_COT_KEYS)
_STEPS_MAP = _label_map(_STEPS_KEYS)


def _choice_keys(kind):
    return {"cot": _COT_KEYS, "cot_ext": _COT_KEYS[:2], "steps": _STEPS_KEYS}[kind]


def _choice_default(kind):
    return {"cot": "full", "cot_ext": "full", "steps": "best"}[kind]


def _choice_labels(kind, lang):
    return [i18n.t(key, lang) for _, key in _choice_keys(kind)]


def _choice_value(kind, code, lang):
    keys = dict(_choice_keys(kind))
    return i18n.t(keys.get(code, keys[_choice_default(kind)]), lang)


def _cot_val(label):
    code = _COT_MAP.get(label, label)
    return code if code in dict(_COT_KEYS) else "full"


def _steps_val(label):
    code = _STEPS_MAP.get(label, label)
    return engine.ODE_STEPS_FAST if code == "fast" else engine.ODE_STEPS_BEST


# === Registry of localizable components ===
_REGISTRY = {}
_SPECS = {}
_ORDER = []


def _reg(key, comp, **spec):
    _REGISTRY[key] = comp
    _SPECS[key] = spec
    _ORDER.append(key)
    return comp


CHOICE_UI_KEYS = ["cot1_in", "cot2_in", "steps1_in", "steps2_in"]


def _ui_update(key, lang, current=None):
    spec = _SPECS[key]
    kw = {}
    if "label" in spec:
        kw["label"] = i18n.t(spec["label"], lang)
    if "info" in spec:
        kw["info"] = i18n.t(spec["info"], lang)
    if "placeholder" in spec:
        kw["placeholder"] = i18n.t(spec["placeholder"], lang)
    if "value" in spec:
        kw["value"] = i18n.t(spec["value"], lang)
    if "recipe" in spec:
        kw["value"] = presets.RECIPE[lang]
    if "choices" in spec:
        kind = spec["choices"]
        kw["choices"] = _choice_labels(kind, lang)
        code = _choice_default(kind)
        for c, k in _choice_keys(kind):
            if current in (i18n.t(k, "en"), i18n.t(k, "ru")):
                code = c
                break
        kw["value"] = _choice_value(kind, code, lang)
    return gr.update(**kw)


def on_switch_lang(lang_choice, *choice_values):
    code = i18n.set_lang("ru" if lang_choice == "RU" else "en")
    current = dict(zip(CHOICE_UI_KEYS, choice_values))
    return [code] + [_ui_update(key, code, current.get(key)) for key in _ORDER]


def _status_tail():
    return engine.last_stage() or engine.vram_info()


def _dur_text(lang=None):
    sec = engine.last_duration_sec()
    if sec <= 0:
        return ""
    return i18n.t("dur_text", lang or i18n.get_lang(),
                   min=f"{sec / 60:.1f}", n=engine.last_tokens())


def _seed_num():
    return state.app_state.last_seed if state.app_state.last_seed is not None else engine.DEFAULT_SEED


def on_generate(lyrics, style, cot, seed, random_seed, steps, lang=None):
    lg = lang or i18n.get_lang()
    if not (lyrics or "").strip():
        return None, i18n.t("err_no_lyrics", lg), engine.vram_info(), None, _seed_num(), _seed_num()
    if not (style or "").strip():
        return None, i18n.t("err_no_style", lg), engine.vram_info(), None, _seed_num(), _seed_num()
    if engine.is_busy():
        return (None, i18n.t("err_busy", lg),
                engine.vram_info(), None, _seed_num(), _seed_num())

    if random_seed:
        used_seed = random.randint(1, 2**31 - 1)
    elif seed is None:
        used_seed = engine.DEFAULT_SEED
    else:
        used_seed = int(seed)

    try:
        result = engine.generate(lyrics, style, cot=_cot_val(cot), seed=used_seed,
                                 steps=_steps_val(steps))
        if not result["ok"]:
            return (None, f"{result['error']} | {_status_tail()}", engine.vram_info(),
                    used_seed, used_seed, used_seed)

        state.app_state.update(result["session_dir"], result["audio_path"], result["abc"],
                               style, lyrics, result["seed"],
                               duration_sec=engine.last_duration_sec(), tokens=engine.last_tokens())
        status = i18n.t("status_done", lg, seed=result["seed"], steps=result["steps"],
                        cot=result["cot"], dur=_dur_text(lg), dir=result["session_dir"],
                        vram=_status_tail())
        return (result["audio_path"], status, engine.vram_info(),
                result["seed"], result["seed"], result["seed"])
    finally:
        engine.clear_vram()


def on_load_score(lang=None):
    lg = lang or i18n.get_lang()
    abc, session_dir = state.load_last_score()
    if not abc:
        return "", i18n.t("err_no_track", lg), state.app_state.seed
    return abc, i18n.t("status_loaded", lg, dir=session_dir), state.app_state.seed


def on_dice():
    return random.randint(1, 2**31 - 1)


def on_rerender(abc_code, cot, steps, seed, style_override, lyrics_override, tempo_pct,
                lang=None):
    lg = lang or i18n.get_lang()
    if not (abc_code or "").strip():
        return (None, i18n.t("err_empty_abc", lg), engine.vram_info(), _seed_num())
    if engine.is_busy():
        return (None, i18n.t("err_busy", lg), engine.vram_info(), _seed_num())
    st = state.app_state
    style_final = (style_override or "").strip() or st.style
    lyrics_final = (lyrics_override or "").strip() or st.lyrics
    if not (style_final or "").strip() or not (lyrics_final or "").strip():
        return (None, i18n.t("err_unknown_ctx_ui", lg), engine.vram_info(), _seed_num())

    used_seed = _seed_num() if seed is None else int(seed)
    notes = []
    abc2 = abc_code
    tempo_pct = int(tempo_pct or 100)
    if tempo_pct != 100:
        if abc_tools.has_tempo(abc2):
            abc2 = abc_tools.rewrite_tempo(abc2, tempo_pct)
            notes.append(i18n.t("note_tempo", lg, pct=tempo_pct))
        else:
            notes.append(i18n.t("note_no_q", lg))
    cot_v = _cot_val(cot)
    if cot_v == "off":
        cot_v = "melody"
        notes.append(i18n.t("note_cot_forced", lg))

    try:
        result = engine.render_from_abc(abc2, style_final, lyrics_final, used_seed,
                                        cot=cot_v, steps=_steps_val(steps))
        if not result["ok"]:
            return None, f"{result['error']} | {_status_tail()}", engine.vram_info(), used_seed

        state.app_state.update(result["session_dir"], result["audio_path"], result["abc"],
                               style_final, lyrics_final, result["seed"],
                               duration_sec=engine.last_duration_sec(), tokens=engine.last_tokens())
        note_txt = f" ({'; '.join(notes)})" if notes else "" 
        status = i18n.t("status_done_notes", lg, notes=note_txt, seed=result["seed"],
                        steps=result["steps"], cot=result["cot"], dur=_dur_text(lg),
                        dir=result["session_dir"], vram=_status_tail())
        return result["audio_path"], status, engine.vram_info(), result["seed"]
    finally:
        engine.clear_vram()


def on_unload_model():
    engine.clear_vram()
    return engine.vram_info()


# === Prompt helper (clickable tag helpers) ===
def _chunks(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def _slug(tag):
    return "".join(c if c.isalnum() else "_" for c in tag).strip("_").lower()


def _make_insert_js(tag, target_id, kind):
    tag_js = json.dumps(tag)
    if kind == "section":
        core = (
            "const s=ta.selectionStart??ta.value.length,e=ta.selectionEnd??ta.value.length;"
            "const before=ta.value.slice(0,s),after=ta.value.slice(e);"
            "const pre=(before==='')?'':(before.endsWith('\\n')?'':'\\n');"
            f"const value=before+pre+{tag_js}+'\\n'+after;"
            f"const pos=(before+pre+{tag_js}+'\\n').length;"
        )
    else:
        core = (
            "const s=ta.selectionStart??ta.value.length,e=ta.selectionEnd??ta.value.length;"
            "const before=ta.value.slice(0,s),after=ta.value.slice(e);"
            "const pre=(before===''||before.endsWith(' ')||before.endsWith(','))?'':', ';"
            f"const value=before+pre+{tag_js}+after;"
            f"const pos=(before+pre+{tag_js}).length;"
        )
    return (
        "() => {"
        f"const ta=document.querySelector('#{target_id} textarea');"
        "if(!ta)return;"
        + core +
        "ta.value=value;ta.selectionStart=ta.selectionEnd=pos;ta.focus();"
        "ta.dispatchEvent(new Event('input',{bubbles:true}));"
        "}"
    )


def _make_tooltips_js():
    payload = json.dumps({"section": presets.TAG_HELP, "style": presets.STYLE_HELP},
                         ensure_ascii=False)
    js = """
() => {
  const HELP = %%PAYLOAD%%;
  let lang = 'en';
  const checked = document.querySelector('#lang_radio input:checked');
  if (checked) {
    const lab = (checked.closest('label') || {}).textContent || '';
    lang = /RU/i.test(lab) ? 'ru' : 'en';
  }
  const apply = (prefix, help) => {
    document.querySelectorAll('[id^="' + prefix + '"]').forEach(btn => {
      const tag = (btn.textContent || '').trim();
      const h = help[tag];
      if (h) btn.title = h[lang] || h.en || '';
    });
  };
  apply('tagbtn_', HELP.section);
  apply('stylebtn_', HELP.style);
}
"""
    return js.replace("%%PAYLOAD%%", payload)


def _build_lyrics_helpers(prefix, lang0, target_id):
    with _reg(f"{prefix}_struct_acc",
              gr.Accordion(i18n.t("struct_acc", lang0), open=False),
              label="struct_acc"):
        _reg(f"{prefix}_struct_hint", gr.Markdown(i18n.t("struct_info", lang0)),
             value="struct_info")
        for chunk in _chunks(presets.SECTION_TAGS, 5):
            with gr.Row():
                for tg in chunk:
                    gr.Button(tg, size="sm", elem_id=f"tagbtn_{_slug(tg)}").click(
                        fn=None, inputs=None, outputs=None,
                        js=_make_insert_js(tg, target_id, "section"))


def _build_style_helpers(prefix, lang0, target_id):
    with _reg(f"{prefix}_style_acc",
              gr.Accordion(i18n.t("style_acc", lang0), open=False),
              label="style_acc"):
        for gname, tags in presets.STYLE_TAGS.items():
            _reg(f"{prefix}_grp_{gname}",
                 gr.Markdown(i18n.t(f"style_grp_{gname}", lang0)),
                 value=f"style_grp_{gname}")
            for chunk in _chunks(tags, 4):
                with gr.Row():
                    for tg in chunk:
                        gr.Button(tg, size="sm", elem_id=f"stylebtn_{_slug(tg)}").click(
                            fn=None, inputs=None, outputs=None,
                            js=_make_insert_js(tg, target_id, "style"))
    with _reg(f"{prefix}_recipe_acc",
              gr.Accordion(i18n.t("recipe_acc", lang0), open=False),
              label="recipe_acc"):
        _reg(f"{prefix}_recipe_md", gr.Markdown(presets.RECIPE[lang0]),
             recipe="recipe")


def build_ui():
    _REGISTRY.clear()
    _SPECS.clear()
    _ORDER.clear()
    lang0 = i18n.get_lang()
    with gr.Blocks(title="YuE2 Web UI Lite") as demo:
        title_md = _reg("title_md", gr.Markdown(i18n.t("app_title", lang0)), value="app_title")
        with gr.Row():
            lang_switch = gr.Radio(choices=["EN", "RU"], value="EN", label="Language",
                                   elem_id="lang_radio")
            unload_btn = _reg("unload_btn", gr.Button(i18n.t("unload_btn", lang0)),
                              value="unload_btn")
            vram_out = _reg("vram_out", gr.Textbox(label=i18n.t("vram_label", lang0),
                               value=engine.vram_info(), interactive=False), label="vram_label")
        lang_state = gr.State("en")
        unload_btn.click(on_unload_model, inputs=None, outputs=[vram_out])

        with _reg("tab1", gr.Tab(i18n.t("tab1", lang0)), label="tab1"):
            _build_lyrics_helpers("t1", lang0, "lyrics1_in")
            lyrics_in = _reg("lyrics_in", gr.Textbox(label=i18n.t("lyrics_label", lang0),
                             lines=10, placeholder=i18n.t("ph_lyrics", lang0),
                             elem_id="lyrics1_in"),
                             label="lyrics_label", placeholder="ph_lyrics")
            style_in = _reg("style_in", gr.Textbox(label=i18n.t("style_label", lang0),
                            placeholder=i18n.t("ph_style", lang0),
                            elem_id="style1_in"),
                            label="style_label", placeholder="ph_style")
            _build_style_helpers("t1", lang0, "style1_in")
            cot1_in = _reg("cot1_in", gr.Dropdown(label=i18n.t("cot_label", lang0),
                            choices=_choice_labels("cot", lang0),
                            value=_choice_value("cot", "full", lang0),
                            info=i18n.t("cot_info", lang0)),
                            label="cot_label", info="cot_info", choices="cot")
            steps1_in = _reg("steps1_in", gr.Radio(label=i18n.t("steps_label", lang0),
                              choices=_choice_labels("steps", lang0),
                              value=_choice_value("steps", "best", lang0),
                              info=i18n.t("steps_info", lang0)),
                              label="steps_label", info="steps_info", choices="steps")
            seed_in = _reg("seed_in", gr.Number(label=i18n.t("seed_label", lang0),
                            value=engine.DEFAULT_SEED, precision=0,
                            info=i18n.t("seed_info", lang0)),
                            label="seed_label", info="seed_info")
            random_seed_in = _reg("random_seed_in", gr.Checkbox(
                label=i18n.t("random_seed_label", lang0), value=False,
                info=i18n.t("random_seed_info", lang0)),
                label="random_seed_label", info="random_seed_info")
            gen_btn = _reg("gen_btn", gr.Button(i18n.t("gen_btn", lang0), variant="primary"),
                           value="gen_btn")
            audio_out = _reg("audio_out", gr.Audio(label=i18n.t("audio_label", lang0),
                             type="filepath"), label="audio_label")
            status_out = _reg("status_out", gr.Textbox(label=i18n.t("status_label", lang0),
                              interactive=False), label="status_label")

        with _reg("tab2", gr.Tab(i18n.t("tab2", lang0)), label="tab2"):
            _reg("tab2_md", gr.Markdown(i18n.t("tab2_desc", lang0)), value="tab2_desc")
            load_btn = _reg("load_btn", gr.Button(i18n.t("load_btn", lang0)),
                            value="load_btn")
            abc_in = _reg("abc_in", gr.Textbox(label=i18n.t("abc_label", lang0), lines=16,
                          placeholder=i18n.t("ph_abc", lang0)),
                          label="abc_label", placeholder="ph_abc")
            with _reg("abc_acc1", gr.Accordion(i18n.t("abc_accordion", lang0), open=False),
                      label="abc_accordion"):
                _reg("abc_help_md1", gr.Markdown(i18n.t("abc_help", lang0)), value="abc_help")
            cot2_in = _reg("cot2_in", gr.Dropdown(label=i18n.t("cot_label", lang0),
                            choices=_choice_labels("cot_ext", lang0),
                            value=_choice_value("cot_ext", "full", lang0),
                            info=i18n.t("cot_info_ext", lang0)),
                            label="cot_label", info="cot_info_ext", choices="cot_ext")
            steps2_in = _reg("steps2_in", gr.Radio(label=i18n.t("steps_label", lang0),
                              choices=_choice_labels("steps", lang0),
                              value=_choice_value("steps", "best", lang0),
                              info=i18n.t("steps_info", lang0)),
                              label="steps_label", info="steps_info", choices="steps")
            seed2_in = _reg("seed2_in", gr.Number(label=i18n.t("seed_label", lang0),
                             value=_seed_num(), precision=0,
                             info=i18n.t("seed2_info", lang0)),
                             label="seed_label", info="seed2_info")
            dice_btn = _reg("dice_btn", gr.Button(i18n.t("dice_btn", lang0)),
                             value="dice_btn")
            with _reg("perf_acc", gr.Accordion(i18n.t("perf_accordion", lang0), open=False),
                      label="perf_accordion"):
                style2_in = _reg("style2_in", gr.Textbox(
                    label=i18n.t("style2_label", lang0), lines=2,
                    placeholder=i18n.t("ph_session", lang0)),
                    label="style2_label", placeholder="ph_session")
                lyrics2_in = _reg("lyrics2_in", gr.Textbox(
                    label=i18n.t("lyrics2_label", lang0), lines=4,
                    placeholder=i18n.t("ph_session", lang0)),
                    label="lyrics2_label", placeholder="ph_session")
                tempo_in = _reg("tempo_in", gr.Slider(label=i18n.t("tempo_label", lang0),
                                minimum=80, maximum=125, value=100, step=5,
                                info=i18n.t("tempo_info", lang0)),
                                label="tempo_label", info="tempo_info")
            rerender_btn = _reg("rerender_btn",
                                gr.Button(i18n.t("rerender_btn", lang0), variant="primary"),
                                value="rerender_btn")
            audio2_out = _reg("audio2_out", gr.Audio(label=i18n.t("audio_label", lang0),
                              type="filepath"), label="audio_label")
            status2_out = _reg("status2_out", gr.Textbox(label=i18n.t("status_label", lang0),
                              interactive=False), label="status_label")

            load_btn.click(on_load_score, inputs=[lang_state],
                           outputs=[abc_in, status2_out, seed2_in])
            dice_btn.click(on_dice, inputs=None, outputs=[seed2_in])
            rerender_btn.click(on_rerender,
                               inputs=[abc_in, cot2_in, steps2_in, seed2_in, style2_in,
                                       lyrics2_in, tempo_in, lang_state],
                               outputs=[audio2_out, status2_out, vram_out, seed2_in])

        attach_tips = _make_tooltips_js()
        demo.load(fn=None, inputs=None, outputs=None, js=attach_tips)
        lang_switch.change(
            on_switch_lang,
            inputs=[lang_switch] + [_REGISTRY[k] for k in CHOICE_UI_KEYS],
            outputs=[lang_state] + [_REGISTRY[k] for k in _ORDER]
        ).then(fn=None, inputs=None, outputs=None, js=attach_tips)

        gen_btn.click(on_generate,
                      inputs=[lyrics_in, style_in, cot1_in, seed_in, random_seed_in,
                              steps1_in, lang_state],
                      outputs=[audio_out, status_out, vram_out, seed_in, seed2_in])
    return demo


if __name__ == "__main__":
    print("[WebUI] Loading YuE2-3B model into VRAM (once)...")
    engine.get_pipeline()
    print("[WebUI] Model loaded. Server: http://127.0.0.1:9099")
    demo = build_ui()
    demo.queue()
    demo.launch(server_name="127.0.0.1", server_port=9099)
