import pytest

from nagrica.grid.boards    import Board, LinkedBoard


# Add new Board implementations here to run every board-agnostic test against them
BOARDS: list[type[Board]] = [LinkedBoard]


@pytest.fixture(params=BOARDS, ids=lambda cls: cls.__name__)
def board_class(request: pytest.FixtureRequest) -> type[Board]:
    return request.param
