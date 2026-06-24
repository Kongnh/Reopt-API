"""Versioned Vietnam proforma defaults.

Loads ``vietnam_defaults.json`` once at import. Modules expose the public
``DEFAULT_*`` / regulatory constants from these values, so the single
externally-editable file is the source of the numbers while the code keeps the
regulatory provenance in comments. Mirrors SAM's ``deploy/runtime/defaults``.
"""

import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "vietnam_defaults.json")

with open(_PATH, encoding="utf-8") as _f:
    _DEFAULTS = json.load(_f)

VERSION = _DEFAULTS["version"]
FINANCIAL_DEFAULTS = _DEFAULTS["financial"]
TAX_DEFAULTS = _DEFAULTS["tax"]
