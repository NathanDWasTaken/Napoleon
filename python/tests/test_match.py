from nagrica.game       import Match, BasicGameState, CompleteGameState, Player
from nagrica.grid       import Board, Edge
from nagrica.ai         import RandomMove
from nagrica.players    import ComputerPlayer


def random_players(*seeds: int) -> list[ComputerPlayer]:
    return [
        ComputerPlayer(f"Player {seat + 1}", seat, search_algo=RandomMove(seed=seed))
        for seat, seed in enumerate(seeds)
    ]


def test_match_plays_to_the_end(board_class: type[Board]):
    match = Match(random_players(1, 2), height=4, width=5, board_class=board_class)

    match.game_loop()

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

    first.game_loop()
    second.game_loop()

    assert first.state.history  == second.state.history
    assert first.state.scores   == second.state.scores


class MeddlingPlayer(Player):
    """Plays a few moves on the state it is given, then picks the next one."""

    def make_move(self, gameState: CompleteGameState) -> Edge:
        for _ in range(3):
            gameState.apply(gameState.legal_moves()[0])

        return gameState.legal_moves()[0]


class RecordingPlayer(Player):
    """Records every state it is handed, then plays the first legal move."""

    def __init__(self, name: str, seat: int) -> None:
        self.seen: list[CompleteGameState] = []

        super().__init__(name, seat)

    def make_move(self, gameState: CompleteGameState) -> Edge:
        self.seen.append(gameState)

        return gameState.legal_moves()[0]


class RecordingSearch(RandomMove):
    """Random search that records every state it is asked to search."""

    def __init__(self, seed: int) -> None:
        self.seen: list[BasicGameState] = []

        super().__init__(seed=seed)

    def select_move(self, gameState: BasicGameState) -> Edge:
        self.seen.append(gameState)

        return super().select_move(gameState)


def test_match_keeps_a_complete_state(board_class: type[Board]):
    match = Match(random_players(1, 2), height=3, width=3, board_class=board_class)

    assert type(match.state) is CompleteGameState


def test_players_are_handed_a_complete_copy(board_class: type[Board]):
    # Players such as humans need ownership to show the board, so they get the complete state
    players = [RecordingPlayer("A", 0), RecordingPlayer("B", 1)]
    match   = Match(players, height=3, width=3, board_class=board_class)

    match.game_loop()

    seen = players[0].seen + players[1].seen

    assert seen
    assert all(type(state) is CompleteGameState for state in seen)
    assert all(state is not match.state for state in seen)


def test_computer_players_search_basic_states(board_class: type[Board]):
    # Engines only get the basic state, so they skip the ownership bookkeeping
    searches    = [RecordingSearch(1), RecordingSearch(2)]
    players     = [ComputerPlayer(f"CPU {seat}", seat, search_algo=search) for seat, search in enumerate(searches)]
    match       = Match(players, height=3, width=3, board_class=board_class)

    match.game_loop()

    seen = searches[0].seen + searches[1].seen

    assert seen
    assert all(type(state) is BasicGameState for state in seen)


def test_finished_match_tracks_ownership(board_class: type[Board]):
    match = Match(random_players(3, 4), height=4, width=5, board_class=board_class)

    match.game_loop()

    assert len(match.state.captured) == 20

    for seat, score in enumerate(match.state.scores):
        assert list(match.state.captured.values()).count(seat) == score


    assert match.state.placed == {wall: turn.player_seat for turn in match.state.history if (wall := turn.wall) is not None}
    assert len(match.state.placed) == sum(turn.wall is not None for turn in match.state.history)


def test_players_cannot_change_the_real_game(board_class: type[Board]):
    # Players are handed a copy, so meddling with it must not touch the match state
    match   = Match([MeddlingPlayer("A", 0), MeddlingPlayer("B", 1)], height=4, width=4, board_class=board_class)
    state   = match.state
    player  = match.current_player

    player.make_move(state.copy())

    assert state.history        == []
    assert state.scores         == [0, 0]
    assert state.board.num_in_play == 16
