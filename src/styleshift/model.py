"""Model loading and text rewriting."""

from __future__ import annotations

import logging
import threading
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from styleshift.config import MODEL_ID
from styleshift.styles import STYLES, StyleSpec

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты перефразируешь текст, меняя только стиль. "
    "Строгие правила: сохраняй смысл 1-в-1, не добавляй новых фактов, "
    "не пиши стихи сверх задания, не объясняй. "
    "Ответ — только переписанный текст, примерно той же длины."
)

FEW_SHOT_USER = (
    "Стиль: деловой\n"
    "Исходный текст: привет, завтра сможешь глянуть мой отчёт? "
    "а то я уже не вдупляю\n"
    "Перефраз:"
)

FEW_SHOT_ASSISTANT = (
    "Здравствуйте! Не могли бы вы завтра ознакомиться с моим отчётом? "
    "У меня возникли сложности с его пониманием."
)


class ModelService:
    """Thread-safe wrapper around the causal LM used for rewriting."""

    def __init__(self, model_id: str = MODEL_ID) -> None:
        self.model_id = model_id
        self.tokenizer: Any = None
        self.model: Any = None
        self.status = "loading"
        self.error: str | None = None
        self._lock = threading.Lock()

    def load(self) -> None:
        """Download (if needed) and load the model into memory."""
        try:
            logger.info("Loading model %s...", self.model_id)
            logger.info(
                "On first run the model will be downloaded — "
                "this may take a few minutes"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                dtype=torch.float32,
                device_map="cpu",
            )
            self.model.eval()
            self.status = "ready"
            logger.info("Model is ready.")
        except Exception as exc:
            self.status = "error"
            self.error = str(exc)
            logger.exception("Failed to load model: %s", exc)

    def start_background_load(self) -> None:
        """Start model loading in a daemon thread."""
        thread = threading.Thread(target=self.load, daemon=True, name="model-loader")
        thread.start()

    def rewrite(self, text: str, style: str) -> str:
        """Rewrite *text* into the requested *style*."""
        if self.status != "ready" or self.tokenizer is None or self.model is None:
            raise RuntimeError("Model is not ready")
        if style not in STYLES:
            raise ValueError(f"Unknown style: {style}")

        style_info: StyleSpec = STYLES[style]
        source = text.strip()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": FEW_SHOT_USER},
            {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
            {
                "role": "user",
                "content": (
                    f"Стиль: {style_info['label'].lower()}\n"
                    f"Задание: {style_info['instruction']}\n"
                    f"Исходный текст: {source}\n"
                    "Перефраз:"
                ),
            },
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt")
        max_new = min(220, max(48, int(len(source.split()) * 4) + 32))

        with self._lock, torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=True,
                temperature=0.3,
                top_p=0.8,
                repetition_penalty=1.12,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
        return clean_reply(self.tokenizer.decode(new_tokens, skip_special_tokens=True))


def clean_reply(text: str) -> str:
    """Strip common model preamble from the generated reply."""
    text = (text or "").strip()
    prefixes = (
        "вот переписанный текст:",
        "переписанный текст:",
        "результат:",
        "ответ:",
    )
    lowered = text.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            text = text[len(prefix) :].strip()
            break
    return text.strip(" «»\"'")
