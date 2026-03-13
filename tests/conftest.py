from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient를 세션 범위로 제공하는 공용 픽스처.
    """
    with TestClient(app) as c:
        yield c

