"""CLI entrypoint: ``python -m styleshift`` or ``styleshift``."""

from __future__ import annotations

import logging
import sys

from styleshift.app import create_app
from styleshift.config import HOST, PORT
from styleshift.model import ModelService


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    service = ModelService()
    service.start_background_load()

    app = create_app(service)
    print(f"\nСервис стилей текста: http://{HOST}:{PORT}\n", flush=True)
    app.run(host=HOST, port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
