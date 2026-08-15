"""Compatibility alias for the renamed ``libretto_tools`` package."""

import libretto_tools as _libretto_tools
from libretto_tools import __version__

__all__ = ["__version__"]
__path__ = _libretto_tools.__path__
