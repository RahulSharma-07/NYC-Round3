"""
Deprecated — use `python -m pc_use` or `pc-use` instead.

This file is kept for backwards compatibility.
"""
import sys
import warnings

warnings.warn(
    "demo.py is deprecated. Use `python -m pc_use` or `pc-use` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from pc_use.cli import main  # noqa: E402

sys.exit(main())
