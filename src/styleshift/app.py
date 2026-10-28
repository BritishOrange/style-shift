"""Flask application factory and HTTP routes."""

from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

from styleshift.config import MAX_TEXT_LENGTH, MODEL_ID, PUBLIC_DIR
from styleshift.model import ModelService
from styleshift.styles import STYLES, list_styles


def create_app(model_service: ModelService | None = None) -> Flask:
    """Create and configure the Flask application."""
    service = model_service or ModelService()
    app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path="")
    app.extensions["model_service"] = service

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/styles")
    def styles():
        return jsonify(list_styles())

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": service.status,
                "model": MODEL_ID,
                "error": service.error,
            }
        )

    @app.post("/api/rewrite")
    def rewrite():
        if service.status != "ready":
            msg = {
                "loading": "Модель ещё загружается. Подождите немного.",
                "error": service.error or "Модель недоступна.",
            }.get(service.status, "Сервис не готов.")
            return jsonify({"error": msg}), 503

        data = request.get_json(silent=True) or {}
        text = data.get("text")
        style = data.get("style")

        if not isinstance(text, str) or not text.strip():
            return jsonify({"error": "Введите текст."}), 400
        if style not in STYLES:
            return jsonify({"error": "Выберите стиль."}), 400
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify(
                {
                    "error": (
                        f"Текст слишком длинный (макс. {MAX_TEXT_LENGTH} символов)."
                    )
                }
            ), 400

        rewritten = service.rewrite(text, style)
        if not rewritten:
            return jsonify(
                {"error": "Модель вернула пустой ответ. Попробуйте ещё раз."}
            ), 500

        style_info = STYLES[style]
        return jsonify(
            {
                "original": text.strip(),
                "style": style,
                "styleLabel": style_info["label"],
                "rewritten": rewritten,
            }
        )

    return app
