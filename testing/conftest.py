
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def testing_path() -> Path:
    return Path("./testing")

@pytest.fixture(scope="session")
def tmp_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("tmp")