"""Development import shim for the Contextix package.

The production package maps `contextix` to `src` through `pyproject.toml`.
This shim lets the repository run without installation in minimal Python
environments where `pip` is unavailable.
"""

from pathlib import Path

_src_package = Path(__file__).resolve().parent.parent / "src"
if _src_package.exists():
    __path__.append(str(_src_package))

__version__ = "0.1.0"
