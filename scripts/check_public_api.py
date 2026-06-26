"""Audit the public API surface.

Fails (exit 1) if:
  * a name in ``tokenhelm.__all__`` is not importable, or
  * a public symbol is undocumented in ``docs/api-reference.md``.

Run via ``nox -s docs`` or ``python scripts/check_public_api.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import tokenhelm

API_DOC = Path(__file__).resolve().parent.parent / "docs" / "api-reference.md"

# Names that are real exports but need not be named verbatim in the prose reference.
DOC_EXEMPT = {"__version__"}


def main() -> int:
    errors: list[str] = []
    exported = list(tokenhelm.__all__)

    # 1. Every __all__ name resolves to a real attribute.
    for name in exported:
        if not hasattr(tokenhelm, name):
            errors.append(f"__all__ lists {name!r} but it is not importable from tokenhelm")

    # 2. Every public symbol is documented.
    doc_text = API_DOC.read_text(encoding="utf-8")
    for name in exported:
        if name in DOC_EXEMPT:
            continue
        if name not in doc_text:
            errors.append(f"{name!r} is exported but not documented in {API_DOC.name}")

    # 3. No accidental private names in __all__.
    for name in exported:
        if name.startswith("_") and name not in DOC_EXEMPT:
            errors.append(f"{name!r} looks private but is exported")

    print(f"Public exports audited: {len(exported)}")
    print("  " + ", ".join(exported))
    if errors:
        print("\nAPI AUDIT FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("\nAPI audit OK: all exports importable and documented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
