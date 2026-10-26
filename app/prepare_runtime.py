"""Genero en el build la caché de fuentes de Matplotlib para no hacerlo en el arranque en frío.
Lo ejecuto con: python -m app.prepare_runtime"""

import os
import time

import matplotlib.font_manager  # noqa: F401  (importarlo construye la caché si no existe)


def main() -> None:
    started = time.time()
    matplotlib.font_manager.fontManager  # noqa: B018
    print(f"matplotlib cache ready in {os.environ['MPLCONFIGDIR']} ({time.time() - started:.1f}s)")


if __name__ == "__main__":
    main()
