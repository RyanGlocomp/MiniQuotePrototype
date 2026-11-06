import shutil
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]
ROOT = API_DIR.parent
sys.path.insert(0, str(API_DIR))


@pytest.fixture
def root() -> Path:
    return ROOT


def pytest_collection_modifyitems(config, items):
    if shutil.which("soffice"):
        return
    skip = pytest.mark.skip(reason="soffice not on PATH")
    for item in items:
        if "libreoffice" in item.keywords:
            item.add_marker(skip)
