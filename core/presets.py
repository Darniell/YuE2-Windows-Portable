"""Шпаргалки промптов YuE2: теги структуры лирики и конструктор стиля.

Чистый модуль (без gradio): используется app.py (кликабельные кнопки-аккордеоны)
и tests/test_prompt_helper.py. Теги всегда EN — так их понимает модель;
подписи аккордеонов/групп локализуются в core/i18n.py.
Вставка тегов — клиентская (JS в app.py, в место курсора); здесь только данные.
"""

# Секции лирики: вставляются в место курсора lyrics-поля собственной строкой
# (в пустом поле тег становится первой строкой).
SECTION_TAGS = ["[Intro]", "[Verse]", "[Pre-Chorus]", "[Chorus]", "[Post-Chorus]",
                "[Bridge]", "[Interlude]", "[Solo]", "[Outro]"]

# Теги стиля по группам: вставляются в место курсора style-поля через ", "
# (первое значение в пустом поле — без запятой).
STYLE_TAGS = {
    "genre": ["rock", "symphonic rock", "orchestral metal", "indie pop",
              "synth-pop", "acoustic folk", "power ballad", "alt rock"],
    "vocal": ["male vocal", "female vocal", "deep male vocal", "airy female vocal",
              "choir backing", "duet"],
    "lead": ["prominent cello", "solo violin", "strings section", "piano",
             "synth lead", "distorted guitar", "acoustic guitar", "saxophone"],
    "rhythm": ["driving drums", "slow groove", "4/4 beat", "double-kick drums",
               "acoustic strumming", "tribal percussion"],
    "mood": ["epic", "melancholic", "energetic", "dreamy", "dark", "triumphant"],
}

# Hover-подсказки тегов структуры: тег -> {"en": ..., "ru": ...}
# (что делает тег + варианты написания/заполнения).
TAG_HELP = {
    "[Intro]": {
        "en": "Instrumental opening; sets the key and tempo. Variants: short intro "
              "or 'instrumental intro' line after the tag.",
        "ru": "Инструментальное вступление; задаёт тональность и темп. Варианты: "
              "короткий интро или строка 'instrumental intro' после тега.",
    },
    "[Verse]": {
        "en": "Main narrative section; the story lives here. ~4-8 lines; repeat "
              "the tag before each new verse ([Verse] ... [Verse] ...).",
        "ru": "Основной повествовательный куплет; здесь живёт сюжет. ~4-8 строк; "
              "повторяйте тег перед каждым новым куплетом ([Verse] ... [Verse] ...).",
    },
    "[Pre-Chorus]": {
        "en": "Build-up before the chorus: rising tension, shorter lines. Variants: "
              "[Pre-Chorus] / [Prechorus] / [Lift].",
        "ru": "Разгон перед припевом: растущее напряжение, более короткие строки. "
              "Варианты: [Pre-Chorus] / [Prechorus] / [Lift].",
    },
    "[Chorus]": {
        "en": "The hook: main refrain with the title line. Repeat the tag for each "
              "chorus; keep the words identical between repeats.",
        "ru": "Хук: главный припев со строкой-названием. Повторяйте тег для каждого "
              "припева; слова между повторами держите одинаковыми.",
    },
    "[Post-Chorus]": {
        "en": "Short tail after the chorus: vocal riff or instrumental hook. "
              "Variants: [Post-Chorus] / [Drop] (for electronic styles).",
        "ru": "Короткий хвост после припева: вокальная распевка или инструментальный "
              "хук. Варианты: [Post-Chorus] / [Drop] (для электроники).",
    },
    "[Bridge]": {
        "en": "Contrasting section before the final chorus; usually quieter, different "
              "melody/harmony. Variants: [Bridge] / [Middle 8].",
        "ru": "Контрастная секция перед финальным припевом; обычно тише, другая "
              "мелодия/гармония. Варианты: [Bridge] / [Middle 8].",
    },
    "[Interlude]": {
        "en": "Instrumental passage between sections; instrument set in style or "
              "described on the line after the tag. Variants: [Interlude] / [Break].",
        "ru": "Инструментальная связка между секциями; инструмент задаётся в style "
              "или строкой после тега. Варианты: [Interlude] / [Break].",
    },
    "[Solo]": {
        "en": "Instrumental solo; the instrument is set in style (guitar/violin/piano) "
              "or written on a line after the tag, e.g. 'electric guitar solo'.",
        "ru": "Инструментальное соло; инструмент задаётся в style (guitar/violin/piano) "
              "или строкой после тега, например 'electric guitar solo'.",
    },
    "[Outro]": {
        "en": "Closing section: fade-out or final phrase. Variants: [Outro] / "
              "[Fade Out] / [End].",
        "ru": "Завершающая секция: затухание или финальная фраза. Варианты: [Outro] / "
              "[Fade Out] / [End].",
    },
}

# Hover-подсказки тегов стиля: тег -> {"en": ..., "ru": ...} (однострочные).
STYLE_HELP = {
    # genre
    "rock": {
        "en": "Straight rock groove; add a subgenre (alt, symphonic) for flavor.",
        "ru": "Прямой рок-грув; уточняйте поджанр (alt, symphonic) для оттенка.",
    },
    "symphonic rock": {
        "en": "Rock band + orchestral strings; vocals stay rock, not operatic.",
        "ru": "Рок-группа + оркестровые струнные; вокал роковый, не оперный.",
    },
    "orchestral metal": {
        "en": "Heavy metal with a full orchestra; epic and dense.",
        "ru": "Хэви-метал с полным оркестром; эпично и плотно.",
    },
    "indie pop": {
        "en": "Light jangly pop with lo-fi warmth.",
        "ru": "Лёгкий звенящий поп с тёплым lo-fi.",
    },
    "synth-pop": {
        "en": "80s-style synths over a steady dance beat.",
        "ru": "Синты в духе 80-х поверх ровного танцевального бита.",
    },
    "acoustic folk": {
        "en": "Acoustic guitars, organic and intimate.",
        "ru": "Акустические гитары, органично и камерно.",
    },
    "power ballad": {
        "en": "Slow emotive rock anthem with a big final chorus.",
        "ru": "Медленная эмоциональная рок-баллада с большим финальным припевом.",
    },
    "alt rock": {
        "en": "Alternative rock: wide dynamics, rougher edge.",
        "ru": "Альтернативный рок: широкая динамика, более грубый край.",
    },
    # vocal
    "male vocal": {
        "en": "Lead vocal sung by a male voice.",
        "ru": "Ведущий вокал в мужском голосе.",
    },
    "female vocal": {
        "en": "Lead vocal sung by a female voice.",
        "ru": "Ведущий вокал в женском голосе.",
    },
    "deep male vocal": {
        "en": "Low male voice (baritone/bass).",
        "ru": "Низкий мужской голос (баритон/бас).",
    },
    "airy female vocal": {
        "en": "Light, breathy female voice.",
        "ru": "Лёгкий, воздушный женский голос.",
    },
    "choir backing": {
        "en": "Backing choir behind the lead vocal.",
        "ru": "Бэк-хор за ведущим вокалом.",
    },
    "duet": {
        "en": "Two alternating lead voices (male + female).",
        "ru": "Два чередующихся ведущих голоса (мужской + женский).",
    },
    # lead
    "prominent cello": {
        "en": "Cello as a leading orchestral voice.",
        "ru": "Виолончель как ведущий оркестровый голос.",
    },
    "solo violin": {
        "en": "Featured violin line over the arrangement.",
        "ru": "Выдвинутая вперёд линия скрипки.",
    },
    "strings section": {
        "en": "Full string ensemble accompaniment.",
        "ru": "Полный струнный ансамбль в аккомпанементе.",
    },
    "piano": {
        "en": "Piano-driven arrangement.",
        "ru": "Аранжировка с ведущим фортепиано.",
    },
    "synth lead": {
        "en": "Synthesizer carries the main melodic line.",
        "ru": "Синтезатор ведёт основную мелодическую линию.",
    },
    "distorted guitar": {
        "en": "Overdriven electric guitar in the foreground.",
        "ru": "Перегруженная электрогитара на переднем плане.",
    },
    "acoustic guitar": {
        "en": "Clean acoustic guitar in the foreground.",
        "ru": "Чистая акустическая гитара на переднем плане.",
    },
    "saxophone": {
        "en": "Sax as a lead or featured instrument.",
        "ru": "Саксофон как ведущий или солирующий инструмент.",
    },
    # rhythm
    "driving drums": {
        "en": "Pushing, energetic drum pattern.",
        "ru": "Мотающий, энергичный барабанный паттерн.",
    },
    "slow groove": {
        "en": "Relaxed mid-tempo groove (fits 80-100 bpm).",
        "ru": "Расслабленный мид-темп грув (уместен на 80-100 bpm).",
    },
    "4/4 beat": {
        "en": "Plain four-on-the-floor meter.",
        "ru": "Прямая четырёхдольная сетка.",
    },
    "double-kick drums": {
        "en": "Fast double-bass drumming (metal, 140+ bpm).",
        "ru": "Быстрая двойная бочка (метал, 140+ bpm).",
    },
    "acoustic strumming": {
        "en": "Strummed acoustic guitar as the rhythmic base.",
        "ru": "Бой акустической гитары как ритм-основа.",
    },
    "tribal percussion": {
        "en": "Hand drums and ethnic percussion.",
        "ru": "Ручные барабаны и этническая перкуссия.",
    },
    # mood
    "epic": {
        "en": "Grand, cinematic scale.",
        "ru": "Грандиозный, кинематографичный масштаб.",
    },
    "melancholic": {
        "en": "Sad, wistful atmosphere.",
        "ru": "Грустное, щемящее настроение.",
    },
    "energetic": {
        "en": "High-energy, driving feel.",
        "ru": "Высокая энергия, заводной характер.",
    },
    "dreamy": {
        "en": "Soft, floating, reverb-heavy atmosphere.",
        "ru": "Мягкая, парящая атмосфера с реверберацией.",
    },
    "dark": {
        "en": "Minor key, brooding tone.",
        "ru": "Минорный, мрачный тон.",
    },
    "triumphant": {
        "en": "Victorious, uplifting mood.",
        "ru": "Победное, возвышающее настроение.",
    },
}

# Порядок стиль-промпта + темповая шкала; рендерится в аккордеоне "Prompt recipe".
RECIPE = {
    "en": (
        "**Style prompt order:**\n\n"
        "`genre` -> `tempo` -> `vocal` -> `lead instrument` -> `accompaniment` -> `mood`\n\n"
        "**Tempo guide:** `60-80 bpm` — ballads, doom; `80-100` — slow groove, hip-hop; "
        "`100-120` — mid-tempo rock, indie, pop; `120-140` — dance, energetic pop-rock; "
        "`140-160+` — punk, metal, double-kick. Tempo is written in style as `N bpm`.\n\n"
        "**Good prompt example:**\n\n"
        "`symphonic rock, 120 bpm, female vocal, prominent cello, "
        "orchestral accompaniment, epic`\n\n"
        "**Lyrics volume:** ~5-6 lines per minute of audio; each section ~4 lines."
    ),
    "ru": (
        "**Порядок стиль-промпта:**\n\n"
        "`жанр` -> `темп` -> `вокал` -> `ведущий инструмент` -> `аккомпанемент` -> `настроение`\n\n"
        "**Темповая шкала:** `60-80 bpm` — баллады, дум; `80-100` — медленный грув, "
        "hip-hop; `100-120` — мид-темп рок, инди, поп; `120-140` — танцевальный, "
        "энергичный поп-рок; `140-160+` — панк, метал, double-kick. Темп указывается "
        "в style как `N bpm`.\n\n"
        "**Пример хорошего промпта:**\n\n"
        "`symphonic rock, 120 bpm, female vocal, prominent cello, "
        "orchestral accompaniment, epic`\n\n"
        "**Объём лирики:** ~5-6 строк на минуту аудио; секция — ~4 строки."
    ),
}
