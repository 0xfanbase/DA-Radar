"""Shared pytest fixtures.

No test in this suite may touch a live network endpoint -- mocked HTTP
(via requests-mock) never opens a real socket in the first place, and this
autouse fixture makes that structural rather than just conventional, so a
future test can't silently start hitting a live feed in CI.
"""
from __future__ import annotations

import os
import socket

import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
HK_JURISDICTION_PATH = os.path.join(REPO_ROOT, "config", "jurisdiction.json")
FREEDONIA_JURISDICTION_PATH = os.path.join(FIXTURES_DIR, "second_jurisdiction.json")


@pytest.fixture(autouse=True)
def _block_real_network(monkeypatch):
    def _guard(*args, **kwargs):
        raise RuntimeError(
            "Real network access attempted during a test -- use the requests_mock "
            "fixture instead of hitting a live endpoint."
        )

    monkeypatch.setattr(socket.socket, "connect", _guard)


@pytest.fixture
def fixture_path():
    def _path(name: str) -> str:
        return os.path.join(FIXTURES_DIR, name)

    return _path


@pytest.fixture
def fixture_bytes(fixture_path):
    def _load(name: str) -> bytes:
        with open(fixture_path(name), "rb") as fh:
            return fh.read()

    return _load
