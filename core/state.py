"""Глобальное состояние сессии: пути к последним артефактам генерации."""
import json
from pathlib import Path

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"


class AppState:
    def __init__(self):
        self.session_dir = None
        self.audio_path = None
        self.abc = None
        self.style = None
        self.lyrics = None
        self.seed = None
        self.last_seed = None
        self.duration_sec = None
        self.tokens = None

    def update(self, session_dir, audio_path, abc, style=None, lyrics=None, seed=None,
               duration_sec=None, tokens=None):
        self.session_dir = session_dir
        self.audio_path = audio_path
        self.abc = abc
        self.style = style
        self.lyrics = lyrics
        self.seed = seed
        self.last_seed = seed
        self.duration_sec = duration_sec
        self.tokens = tokens


def _load_request_context(session_dir):
    """Style/Lyrics/seed последней генерации из request.json (переживает рестарт UI)."""
    req = Path(session_dir) / "request.json"
    if not req.is_file():
        return None
    try:
        data = json.loads(req.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data.get("style"), data.get("lyrics"), data.get("seed")


def load_last_score():
    """Вернуть (abc, session_dir) последнего трека: из памяти или из outputs/web_ui_*.

    Заполняет style/lyrics/seed в app_state, необходимые для перерендера.
    """
    st = app_state
    if st.abc:
        if st.style is None and st.session_dir:
            ctx = _load_request_context(st.session_dir)
            if ctx:
                st.style, st.lyrics, st.seed = ctx
        return st.abc, st.session_dir
    sessions = sorted(OUTPUTS_DIR.glob("web_ui_*")) if OUTPUTS_DIR.is_dir() else []
    for session in reversed(sessions):
        score = session / "score.abc"
        if not score.is_file():
            continue
        ctx = _load_request_context(session)
        st.style, st.lyrics, st.seed = ctx if ctx else (None, None, None)
        st.abc = score.read_text(encoding="utf-8")
        st.session_dir = str(session)
        st.audio_path = str(session / "audio.flac")
        return st.abc, st.session_dir
    return None, None


app_state = AppState()
