import os
import tempfile
from pathlib import Path
import pytest

# Isolate test database and ML artifacts before importing app modules
_TEST_DIR = Path(tempfile.mkdtemp(prefix="gayatri_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'test_gayatri.db').as_posix()}"
os.environ["ML_ARTIFACTS_DIR"] = str(_TEST_DIR / "ml_artifacts")
os.environ["SECRET_KEY"] = "test-secret-key-for-automated-suite-32chars"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
