from pathlib import Path


def summarize(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return text[:200]
