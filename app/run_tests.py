"""Corro todas las autoverificaciones del motor (app/test_*.py) en un solo comando y fallo si alguna falla.
Ejecutar con: python -m app.run_tests"""

import pkgutil
import runpy
import sys
import traceback

import app


def main() -> int:
    test_modules = sorted(m.name for m in pkgutil.iter_modules(app.__path__) if m.name.startswith("test_"))
    failed = []
    for name in test_modules:
        try:
            runpy.run_module(f"app.{name}", run_name="__main__")
        except Exception:
            traceback.print_exc()
            failed.append(name)
    print(f"{len(test_modules) - len(failed)}/{len(test_modules)} self-checks OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
