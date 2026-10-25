"""!
********************************************************************************
@file   __init__.py
@brief  Exposes some parts of this python package for public usage.
********************************************************************************
"""

from importlib.metadata import version, PackageNotFoundError

from .config_parser import ConfigParser, ParseException
from .creator import DoxygenCreator, DoxygenCreatorError, PYTHON_PATTERN, DOXYGEN_VERSION, get_cmd_args
from .doxy_py_checker import DoxyPyChecker

try:
    __version__ = version("doxygen-creator")  # single source of truth: version in pyproject.toml
except PackageNotFoundError:
    __version__ = "0.0.0"  # package is not installed

__all__ = [
    "ConfigParser",
    "ParseException",
    "DoxygenCreator",
    "DoxygenCreatorError",
    "DoxyPyChecker",
    "PYTHON_PATTERN",
    "DOXYGEN_VERSION",
    "get_cmd_args",
]
