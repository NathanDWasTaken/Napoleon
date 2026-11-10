import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

pygame = pytest.importorskip("pygame")

from nagrica.ui.gui import App, parse_args


@pytest.fixture
def app():
    pygame.init()
    yield App(parse_args(["--height", "3", "--width", "3", "-p", "human", "-p", "human"]))
    pygame.quit()


def edge_center(app: App, edge) -> tuple[int, int]:
    (x1, y1), (x2, y2) = app.edge_points(edge, *app.layout())

    return (x1 + x2) // 2, (y1 + y2) // 2


def test_edge_at_picks_clicked_wall(app):
    for edge in app.legal_moves():
        assert app.edge_at(edge_center(app, edge), *app.layout()) == edge


def test_click_places_wall_and_passes_turn(app):
    edge = app.legal_moves()[0]

    app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=edge_center(app, edge)))

    assert edge in app.state.placed
    assert app.state.current_seat == 1


def test_draw_whole_game(app):
    while not app.state.finished:
        app.play(app.legal_moves()[0])
        app.draw()

    assert sum(app.state.scores) == 9


def test_computer_moves_by_itself():
    pygame.init()
    app = App(parse_args(["--height", "2", "--width", "2", "-p", "random", "-p", "random"]))

    for _ in range(500):
        app.update()

        if app.state.finished:
            break

        pygame.time.wait(5)

    pygame.quit()

    assert app.state.finished
