from napoleon import Grid, Game


if __name__ == "__main__":
    players = Game(grid=Grid(width=2, height=2))

    players.add_player("Alice")
    players.add_player("Bob")

    players.play()