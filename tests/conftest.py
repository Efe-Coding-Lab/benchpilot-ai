from __future__ import annotations

import pytest

from benchpilot_ai.db import init_db, session_scope


@pytest.fixture()
def db_url(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    init_db(url)
    return url


@pytest.fixture()
def session(db_url):
    with session_scope(db_url) as s:
        yield s
