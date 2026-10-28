"""Available rewrite styles and their prompt instructions."""

from __future__ import annotations

from typing import TypedDict


class StyleSpec(TypedDict):
    label: str
    instruction: str


STYLES: dict[str, StyleSpec] = {
    "academic": {
        "label": "Академический",
        "instruction": (
            "Перепиши текст в академическом научном стиле: формально, точно, "
            "без разговорных слов."
        ),
    },
    "business": {
        "label": "Деловой",
        "instruction": (
            "Перепиши текст в деловом официальном стиле: вежливо, кратко, "
            "профессионально."
        ),
    },
    "informal": {
        "label": "Неформальный",
        "instruction": (
            "Перепиши текст в дружеском неформальном стиле: просто, тепло, "
            "по-человечески."
        ),
    },
    "poetic": {
        "label": "Поэтический",
        "instruction": (
            "Перепиши текст в поэтическом художественном стиле: образно, "
            "красиво, выразительно."
        ),
    },
    "simple": {
        "label": "Простой",
        "instruction": (
            "Перепиши текст максимально просто, короткими предложениями, "
            "чтобы понял школьник."
        ),
    },
    "news": {
        "label": "Новостной",
        "instruction": (
            "Перепиши текст в стиле новостной заметки: нейтрально, по делу, без эмоций."
        ),
    },
}


def list_styles() -> list[dict[str, str]]:
    """Return styles in API-friendly format."""
    return [{"id": key, "label": value["label"]} for key, value in STYLES.items()]
