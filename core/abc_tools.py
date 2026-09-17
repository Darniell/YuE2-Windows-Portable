"""Чистые утилиты над ABC-партитурой (без зависимости от движка и модели)."""
import re

# Строка темпа вида "Q:1/4=120" (после "Q:" может быть любая длительность до "=").
_TEMPO_RE = re.compile(r"^(Q:[^=\n]*=\s*)(\d+)(.*)$", re.MULTILINE)


def has_tempo(abc):
    """True, если в ABC есть строка Q: с числовым BPM."""
    return bool(_TEMPO_RE.search(abc or ""))


def rewrite_tempo(abc, pct):
    """Пересчитать BPM в строке Q: пропорционально (BPM_new = round(BPM * pct/100)).

    Остальные строки ABC не трогаются. Нет строки Q: -> ABC возвращается
    без изменений (проверяйте has_tempo, чтобы пометить это в Status).
    """
    if not abc or pct == 100:
        return abc

    def _sub(m):
        return f"{m.group(1)}{round(int(m.group(2)) * pct / 100)}{m.group(3)}"

    return _TEMPO_RE.sub(_sub, abc)
