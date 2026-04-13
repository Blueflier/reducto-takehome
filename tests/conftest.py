import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


@pytest.fixture
def schema_version(request):
    """Pass --schema=v3 on the CLI to select which extraction to test."""
    return request.config.getoption("--schema", default="v3")


def pytest_addoption(parser):
    parser.addoption(
        "--schema", action="store", default="v3", help="Schema version to test (e.g. v3, v4)"
    )


def load_extract(version: str, pdf_stem: str) -> dict:
    """Load extraction JSON for a given version and PDF."""
    filename = f"{pdf_stem}.{version}.extract.json"
    path = ROOT / "schemas" / version / filename
    if not path.exists():
        pytest.skip(f"Extraction not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def amzn(schema_version):
    return load_extract(schema_version, "AMZN-Q4-2024-Earnings-Release")


@pytest.fixture
def aapl(schema_version):
    return load_extract(schema_version, "_10-Q-Q3-2024-As-Filed")
