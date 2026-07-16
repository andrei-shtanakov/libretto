"""Compatibility alias for the renamed ``libretto_tools`` package."""

import libretto_tools as _libretto_tools
from libretto_tools import *  # noqa: F403

__path__ = _libretto_tools.__path__
