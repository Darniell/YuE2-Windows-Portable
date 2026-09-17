"""Localization: EN/RU dictionaries, t() with fallback, global language."""
CURRENT_LANG = "en"
_WARNED_KEYS = set()

LANG = {
    "en": {
        "app_title": "# YuE2-3B - Text2Music",
        "unload_btn": "Unload Model / Clear VRAM",
        "vram_label": "VRAM",
        "vram_no_cuda": "VRAM: CUDA unavailable",
        "seed_session": "Session seed: {seed}",
        "dur_text": "Duration: ~{min} min (tokens: {n})",
        "err_busy": "Model is busy: a generation is already running. Wait for the current track to finish.",
        "err_no_lyrics": "Specify the song lyrics (Lyrics).",
        "err_no_style": "Specify the style description (Style).",
        "err_empty_score": "Score is empty: load or enter ABC code.",
        "err_cot_off_ext": "No score (cot=off) is incompatible with an external score: the yue2 protocol requires cot=melody/full.",
        "err_unknown_ctx": "Style/Lyrics of the original generation are unknown. Click Load last track or generate the track again.",
        "err_unknown_ctx_ui": "Style/Lyrics of the original generation are unknown: click Load last track or fill Style/Lyrics in Performance settings.",
        "err_generation": "Generation error: {err}",
        "err_render": "Render-from-score error: {err}",
        "gate_error": ("Song ~{min} min (tokens: {tokens}) was not synthesized: {reason}. "
                       "The required mode is unavailable, {free} GB free. "
                       "Shorten the lyric sections to ~3 min or close other GPU applications."),
        "gate_vram": ("Not enough VRAM for synthesis: {free} GB free (need >= 6.0 GB). "
                      "Shorten the lyrics or use cot=melody."),
        "tab1": "Text2Music",
        "tab2": "Score Editor (Advanced)",
        "lyrics_label": "Lyrics",
        "ph_lyrics": "[Verse]\n...\n\n[Chorus]\n...",
        "style_label": "Style",
        "ph_style": "cyberpunk, dark synthwave, deep male vocal, ...",
        "cot_label": "Chain-of-Thought",
        "cot_full": "Full (melody+chords)",
        "cot_melody": "Melody (melody only)",
        "cot_off": "No score (direct generation)",
        "cot_info": "Melody - no chords; No score - direct generation without a score (native cot=off branch)",
        "cot_info_ext": "For an external score the protocol allows only Full/Melody",
        "steps_label": "Render quality (ODE steps)",
        "steps_fast": "Fast (16 steps)",
        "steps_best": "Best (32 steps)",
        "steps_info": "Fast is faster, Best is release quality",
        "seed_label": "Seed",
        "seed_info": "Integer; reproducible generation",
        "random_seed_label": "Random seed every run",
        "random_seed_info": "Ignores the Seed field; the used value returns to the field and to Status",
        "gen_btn": "Generate",
        "audio_label": "Result",
        "status_label": "Status",
        "status_done": ("Done. seed: {seed} | steps: {steps} | cot: {cot} | {dur} | "
                        "Artifacts: {dir} | {vram}"),
        "status_done_notes": ("Done{notes}. seed: {seed} | steps: {steps} | cot: {cot} | "
                              "{dur} | Artifacts: {dir} | {vram}"),
        "struct_acc": "Structure tags (click to insert)",
        "struct_info": ("Click a tag to insert it **at the cursor position**; in an "
                        "empty field the tag becomes the first line. Hover a tag for "
                        "details and spelling variants. Tags are always EN - the "
                        "model is trained on them."),
        "style_acc": "Style builder (click to insert)",
        "style_grp_genre": "Genre",
        "style_grp_vocal": "Vocal",
        "style_grp_lead": "Lead instrument",
        "style_grp_rhythm": "Rhythm section",
        "style_grp_mood": "Mood",
        "recipe_acc": "Prompt recipe",
        "tab2_desc": ("Edit the ABC score of the last track and re-render the audio "
                      "(without regenerating the score from scratch). ABC fixes the composition; "
                      "Seed changes the performance (timbre nuances, phrasing) - "
                      "New take gives another take of the same song."),
        "load_btn": "Load last track",
        "abc_label": "ABC score (score.abc)",
        "ph_abc": "X:1\nT:...\n...",
        "abc_accordion": "What is ABC and how to read it",
        "abc_help": ("**ABC cheat sheet**\n"
                     "- Sections: `% verse` / `% chorus` - marker comments before voice lines.\n"
                     "- Voices: `V: Vocal` - vocal (lyrics below as `w:` lines), `V: Ins` - instrumental.\n"
                     "- Notes: `C D E F G A B`; `^`/`_` - sharp/flat. Duration is a number after the note:\n"
                     "  `C2` - 2 beats, `C` - 1 beat, `C/2` - half.\n"
                     "- Chords go in quotes before a note: `\"Am\"C4`.\n"
                     "- Headers: `X:` number, `T:` title, `Q:1/4=120` - tempo (120 BPM), "
                     "`M:4/4` - meter, `K:Am` - key.\n"
                     "- Song lyrics are not edited here: use the Lyrics field in Performance settings."),
        "seed2_info": "Session seed; New take - random seed of the same track",
        "dice_btn": "New take",
        "perf_accordion": "Performance settings (without touching the score)",
        "style2_label": "Style (empty = session style)",
        "ph_session": "empty - taken from the original generation",
        "lyrics2_label": "Lyrics (empty = session lyrics)",
        "tempo_label": "Tempo, %",
        "tempo_info": "Recalculates BPM in the Q: line; ignored without a Q: line",
        "rerender_btn": "Re-render from score",
        "err_no_track": "Last track not found: first generate a track on the Text2Music tab.",
        "status_loaded": "Score loaded: {dir}",
        "err_empty_abc": "Score is empty: click Load last track or enter ABC code.",
        "note_tempo": "tempo {pct}% (Q: rewritten)",
        "note_no_q": "Q: line not found - tempo slider ignored",
        "note_cot_forced": "external score: cot forced to melody",
    },
    "ru": {
        "app_title": "# YuE2-3B - Текст -> Музыка",
        "unload_btn": "Выгрузить модель / Очистить VRAM",
        "vram_label": "VRAM",
        "vram_no_cuda": "VRAM: CUDA недоступна",
        "seed_session": "Seed сессии: {seed}",
        "dur_text": "Длительность: ~{min} мин (tokens: {n})",
        "err_busy": "Модель занята: уже идёт генерация. Дождитесь завершения текущего трека.",
        "err_no_lyrics": "Укажите текст песни (Lyrics).",
        "err_no_style": "Укажите описание стиля (Style).",
        "err_empty_score": "Партитура пуста: загрузите или введите ABC-код.",
        "err_cot_off_ext": "No score (cot=off) несовместим с внешней партитурой: протокол yue2 требует cot=melody/full.",
        "err_unknown_ctx": "Неизвестны Style/Lyrics исходной генерации. Нажмите Загрузить последний трек или сгенерируйте трек заново.",
        "err_unknown_ctx_ui": "Неизвестны Style/Lyrics исходной генерации: нажмите Загрузить последний трек или заполните Style/Lyrics в Параметрах исполнения.",
        "err_generation": "Ошибка генерации: {err}",
        "err_render": "Ошибка рендера из партитуры: {err}",
        "gate_error": ("Песня ~{min} мин (tokens: {tokens}) не синтезирована: {reason}. "
                       "Требуемый режим недоступен, свободно {free} GB. "
                       "Сократите секции текста до ~3 мин или закройте другие GPU-приложения."),
        "gate_vram": ("Недостаточно VRAM для синтеза: свободно {free} GB (нужно >= 6.0 GB). "
                      "Сократите текст или используйте cot=melody."),
        "tab1": "Текст -> Музыка",
        "tab2": "Редактор партитуры (Advanced)",
        "lyrics_label": "Текст песни (Lyrics)",
        "ph_lyrics": "[Verse]\n...\n\n[Chorus]\n...",
        "style_label": "Стиль (Style)",
        "ph_style": "cyberpunk, dark synthwave, deep male vocal, ...",
        "cot_label": "Chain-of-Thought",
        "cot_full": "Full (мелодия+аккорды)",
        "cot_melody": "Melody (только мелодия)",
        "cot_off": "No score (прямая генерация)",
        "cot_info": "Melody - без аккордов; No score - прямая генерация без партитуры (штатная ветка cot=off)",
        "cot_info_ext": "Для внешней партитуры протокол допускает только Full/Melody",
        "steps_label": "Качество рендера (ODE-шаги)",
        "steps_fast": "Fast (16 шагов)",
        "steps_best": "Best (32 шага)",
        "steps_info": "Fast быстрее, Best - качество релиза",
        "seed_label": "Seed",
        "seed_info": "Целое число; воспроизводимость генерации",
        "random_seed_label": "Случайный seed каждый прогон",
        "random_seed_info": "Игнорирует поле Seed; использованное значение вернётся в поле и в Status",
        "gen_btn": "Сгенерировать",
        "audio_label": "Результат",
        "status_label": "Статус",
        "status_done": ("Готово. seed: {seed} | steps: {steps} | cot: {cot} | {dur} | "
                        "Артефакты: {dir} | {vram}"),
        "status_done_notes": ("Готово{notes}. seed: {seed} | steps: {steps} | cot: {cot} | "
                              "{dur} | Артефакты: {dir} | {vram}"),
        "struct_acc": "Теги структуры (клик - вставить)",
        "struct_info": ("Клик по тегу вставляет его **в место курсора**; в пустом поле "
                        "тег становится первой строкой. Наведите курсор на тег - "
                        "подсказка объяснит, что он делает, и покажет варианты "
                        "написания. Теги всегда EN - на них обучена модель."),
        "style_acc": "Конструктор стиля (клик - вставить)",
        "style_grp_genre": "Жанр",
        "style_grp_vocal": "Вокал",
        "style_grp_lead": "Ведущий инструмент",
        "style_grp_rhythm": "Ритм-секция",
        "style_grp_mood": "Настроение",
        "recipe_acc": "Рецепт промпта",
        "tab2_desc": ("Редактирование ABC-партитуры последнего трека и перерендер аудио "
                      "(без повторной генерации партитуры с нуля). ABC фиксирует композицию; "
                      "Seed меняет исполнение (тембровые нюансы, фразировка) - "
                      "Новый дубль даёт ещё один дубль той же песни."),
        "load_btn": "Загрузить последний трек",
        "abc_label": "ABC-партитура (score.abc)",
        "ph_abc": "X:1\nT:...\n...",
        "abc_accordion": "Что такое ABC и как читать",
        "abc_help": ("**Шпаргалка ABC**\n"
                     "- Секции: `% verse` / `% chorus` - комментарии-разметка перед строками партии.\n"
                     "- Партии: `V: Vocal` - вокальная (слова ниже строками `w:`), "
                     "`V: Ins` - инструментальная.\n"
                     "- Ноты: `C D E F G A B` (до…си); `^`/`_` - диез/бемоль. "
                     "Длительность - цифрой после ноты:\n"
                     "  `C2` - 2 доли, `C` - 1 доля, `C/2` - половина.\n"
                     "- Аккорды - в кавычках перед нотой: `\"Am\"C4`.\n"
                     "- Заголовки: `X:` номер, `T:` название, `Q:1/4=120` - темп (120 BPM), "
                     "`M:4/4` - размер, `K:Am` - тональность.\n"
                     "- Слова песни здесь не правятся: используйте поле Lyrics "
                     "в Параметрах исполнения."),
        "seed2_info": "Seed сессии; Новый дубль - случайный seed того же трека",
        "dice_btn": "Новый дубль",
        "perf_accordion": "Параметры исполнения (не трогая партитуру)",
        "style2_label": "Style (пусто = стиль сессии)",
        "ph_session": "пусто - берётся из исходной генерации",
        "lyrics2_label": "Lyrics (пусто = лирика сессии)",
        "tempo_label": "Темп, %",
        "tempo_info": "Пересчитывает BPM в строке Q:; без строки Q: игнорируется",
        "rerender_btn": "Перерендерить из партитуры",
        "err_no_track": "Последний трек не найден: сначала сгенерируйте трек на вкладке Text2Music.",
        "status_loaded": "Партитура загружена: {dir}",
        "err_empty_abc": "Партитура пуста: нажмите Загрузить последний трек или введите ABC-код.",
        "note_tempo": "темп {pct}% (Q: переписана)",
        "note_no_q": "строка Q: не найдена - слайдер темпа проигнорирован",
        "note_cot_forced": "внешняя партитура: cot принудительно melody",
    },
}


def set_lang(lang):
    global CURRENT_LANG
    CURRENT_LANG = lang if lang in LANG else "en"
    return CURRENT_LANG


def get_lang():
    return CURRENT_LANG


def t(key, lang=None, /, **params):
    language = lang if lang in LANG else CURRENT_LANG
    entry = LANG.get(language, {})
    if key not in entry:
        entry = LANG["en"]
        if key not in entry:
            if key not in _WARNED_KEYS:
                _WARNED_KEYS.add(key)
                print(f"[i18n] WARNING: missing key '{key}'", flush=True)
            return key
    template = entry[key]
    if not params:
        return template
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return template
