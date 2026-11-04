import os

import pytest

from nagrica.grid.boards    import Board, LinkedBoard, BitBoard


# Let exceptions escape pytest so the VS Code debugger breaks on them (set by launch.json)
if os.getenv("_PYTEST_RAISE", "0") != "0":
    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call: pytest.CallInfo[object]) -> None:
        if call.excinfo is not None:
            raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo: pytest.ExceptionInfo[BaseException]) -> None:
        raise excinfo.value


# ---------------------------------------------------------------- implementations under test
#
# Every implementation the test suite runs against is listed here.
# Add a new class to its list to run all tests that use the matching fixture against it.


# Board implementations, used by the `board_class` fixture
BOARDS: list[type[Board]] = [LinkedBoard, BitBoard]


@pytest.fixture(params=BOARDS, ids=lambda cls: cls.__name__)
def board_class(request: pytest.FixtureRequest) -> type[Board]:
    return request.param
