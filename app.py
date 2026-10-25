from __future__ import annotations

import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

ROOT = Path(__file__).resolve().parent
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

STYLES = {
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
            "Перепиши текст в стиле новостной заметки: нейтрально, по делу, "
            "без эмоций."
        ),
    },
}

app = Flask(__name__, static_folder=str(ROOT / "public"), static_url_path="")

tokenizer = None
model = None
model_status = "loading"
model_error = None


def clean_reply(text: str) -> str:
    text = (text or "").strip()
    for prefix in (
        "вот переписанный текст:",
        "переписанный текст:",
        "результат:",
        "ответ:",
    ):
        low = text.lower()
        if low.startswith(prefix):
            text = text[len(prefix) :].strip()
    return text.strip(" «»\"'")


def load_model() -> None:
    global tokenizer, model, model_status, model_error
    try:
        print(f"Загрузка модели {MODEL_ID}...", flush=True)
        print(
            "(При первом запуске модель скачается — это может занять несколько минут)",
            flush=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            dtype=torch.float32,
            device_map="cpu",
        )
        model.eval()
        model_status = "ready"
        print("Модель готова.", flush=True)
    except Exception as exc:
        model_status = "error"
        model_error = str(exc)
        print("Не удалось загрузить модель:", exc, flush=True)


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/styles")
def styles():
    return jsonify([{"id": k, "label": v["label"]} for k, v in STYLES.items()])


@app.get("/api/health")
def health():
    return jsonify({"status": model_status, "model": MODEL_ID, "error": model_error})


@app.post("/api/rewrite")
def rewrite():
    if model_status != "ready":
        msg = {
            "loading": "Модель ещё загружается. Подождите немного.",
            "error": model_error or "Модель недоступна.",
        }.get(model_status, "Сервис не готов.")
        return jsonify({"error": msg}), 503

    data = request.get_json(silent=True) or {}
    text = data.get("text")
    style = data.get("style")

    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Введите текст."}), 400
    if style not in STYLES:
        return jsonify({"error": "Выберите стиль."}), 400
    if len(text) > 2000:
        return jsonify({"error": "Текст слишком длинный (макс. 2000 символов)."}), 400

    style_info = STYLES[style]
    source = text.strip()
    messages = [
        {
            "role": "system",
            "content": (
                "Ты перефразируешь текст, меняя только стиль. "
                "Строгие правила: сохраняй смысл 1-в-1, не добавляй новых фактов, "
                "не пиши стихи сверх задания, не объясняй. "
                "Ответ — только переписанный текст, примерно той же длины."
            ),
        },
        {
            "role": "user",
            "content": (
                "Стиль: деловой\n"
                "Исходный текст: привет, завтра сможешь глянуть мой отчёт? а то я уже не вдупляю\n"
                "Перефраз:"
            ),
        },
        {
            "role": "assistant",
            "content": (
                "Здравствуйте! Не могли бы вы завтра ознакомиться с моим отчётом? "
                "У меня возникли сложности с его пониманием."
            ),
        },
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

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    max_new = min(220, max(48, int(len(source.split()) * 4) + 32))

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new,
            do_sample=True,
            temperature=0.3,
            top_p=0.8,
            repetition_penalty=1.12,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
    rewritten = clean_reply(tokenizer.decode(new_tokens, skip_special_tokens=True))

    if not rewritten:
        return jsonify({"error": "Модель вернула пустой ответ. Попробуйте ещё раз."}), 500

    return jsonify(
        {
            "original": text.strip(),
            "style": style,
            "styleLabel": style_info["label"],
            "rewritten": rewritten,
        }
    )


if __name__ == "__main__":
    threading.Thread(target=load_model, daemon=True).start()
    print("\nСервис стилей текста: http://localhost:3000\n", flush=True)
    app.run(host="127.0.0.1", port=3000, debug=False, threaded=True)
