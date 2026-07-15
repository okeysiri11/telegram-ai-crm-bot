"""Pytest fixtures scaffold — no production side effects."""

import pytest


@pytest.fixture
def scaffold_marker():
    return "architecture_scaffold"
