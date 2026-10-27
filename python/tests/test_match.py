from nagrica.game.match          import Match
from nagrica.grid.boards         import Board
from nagrica.players             import RandomPlayer


def random_players(*seeds: int) -> list[RandomPlayer]:
    return [RandomPlayer(f"Player {seat + 1}", seat, seed) for seat, seed in enumerate(seeds)]


def test_match_plays_to_the_end(board_class: type[Board]):
    match = Match(random_players(1, 2), height=4, width=5, board_class=board_class)

    match.start()

    assert match.state.finished
    assert sum(match.state.scores) == 20


def test_current_player_follows_seat(board_class: type[Board]):
    match = Match(random_players(1, 2, 3), height=3, width=3, board_class=board_class)

    assert match.current_player is match.players[0]

    match.state.apply(match.state.legal_moves()[0])

    assert match.current_seat   == 1
    assert match.current_player is match.players[1]


def test_seeded_matches_are_reproducible(board_class: type[Board]):
    first   = Match(random_players(7, 8), height=5, width=5, board_class=board_class)
    second  = Match(random_players(7, 8), height=5, width=5, board_class=board_class)

    first.start()
    second.start()

    assert first.state.history  == second.state.history
    assert first.state.scores   == second.state.scores
