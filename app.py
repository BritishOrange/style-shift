"""Backward-compatible launcher.

Prefer: ``poetry run styleshift`` or ``python -m styleshift``.
"""

from styleshift.__main__ import main

if __name__ == "__main__":
    main()
