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


# Add new Board implementations here to run every board-agnostic test against them
BOARDS: list[type[Board]] = [LinkedBoard, BitBoard]


@pytest.fixture(params=BOARDS, ids=lambda cls: cls.__name__)
def board_class(request: pytest.FixtureRequest) -> type[Board]:
    return request.param
