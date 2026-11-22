"""Ermöglicht ``python -m gradweight_guardrails``."""

from __future__ import annotations

import sys

from .cli import main

sys.exit(main())
