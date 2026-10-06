"""Nutrition Data Foundation executable namespace.

Scientific meaning is owned upstream by the NDF specifications.
This package is a reference implementation only.
"""

from .d0 import run_fixture_suite, validate_fixture

__all__ = ["run_fixture_suite", "validate_fixture"]
