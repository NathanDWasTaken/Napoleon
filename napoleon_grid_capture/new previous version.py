# pos is a coordinate in the form (x, y)
from copy import deepcopy, copy
from random import choice
from time import time
from math import floor

import cProfile, ujson

def subtract_2_addresses(coord1, coord2, operation="-"):
    """do operation element wise between coord1 and coord2"""
    difference = []

    for element2, element1 in zip(coord2, coord1):
        if operation == "-":
            result = element2 - element1
        elif operation == "+":
            result = element2 + element1

        difference.append(result)

    return tuple(difference)

# returns either:
# - the variation of coordinate when going a certain direction
# - the direction for a certain variation in coords

# east -> x + 1 | x + 1 -> east
variation_direction = {
    "n": (0, -1), (0, -1): "n", 
    "e": (1, 0), (1, 0): "e", 
    "s": (0, 1), (0, 1): "s", 
    "w": (-1, 0), (-1, 0): "w"
}
    
opposite_direction = {"n" : "s", "e" : "w", "s" : "n", "w" : "e"}

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.captured = False
        self.visited = False
        
        self.walls = {"n" : None, "e" : None, "s" : None, "w" : None}

    def __deepcopy__(self, memodict={}):
        tile = Tile(self.x, self.y)
        tile.captured = self.captured
        tile.visited = self.visited

        tile.walls = copy(self.walls)

        return tile

class Border:
    pass


class Wall(Border):
    pass


class Grid:
    def __init__(self, width=8, height=8):
        if 1 < width and 1 < height:
            self.width, self.height = width, height
            self.grid = []
            self.tiles_left = []

        else:
            print("Both grid dimensions have to be bigger than 1")

    def create_grid(self):
        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile = Tile(x, y)

                if y == 0:
                    tile.walls["n"] = Border()
                if x == self.width - 1:
                    tile.walls["e"] = Border()
                if y == self.height - 1:
                    tile.walls["s"] = Border()
                if x == 0:
                    tile.walls["w"] = Border()

                self.tiles_left.append(tile)
                row.append(tile)
            self.grid.append(row)

        self.total_n_of_moves = self.height * (self.width - 1) + self.width * (self.height - 1)
        print(f"All possible amount of moves:", self.total_n_of_moves)

    def add_wall(self, coord1, direction):
        """adds a wall to the tile object if it doesn't have one yet"""

        if not self.is_valid_position(coord1):
            print("Address 1 is invalid:", coord1)
            return False

        variation = variation_direction[direction]

        # we can figure out coords of addr2 if we know addr1 and the direction it wants to go
        coord2 = subtract_2_addresses(coord1, variation, operation="+")
        if not self.is_valid_position(coord2):
            print("Address 2 is not Valid")
            return False

        tile1 = self.get_tile(coord1)
        tile2 = self.get_tile(coord2)

        if not (tile1.captured or tile2.captured) and tile1.walls[direction] == tile2.walls[opposite_direction[direction]] == None:
            wall = Wall()
            tile1.walls[direction] = wall
            tile2.walls[opposite_direction[direction]] = wall

            return True

        return False

    def apply_flood_fill(self, coord):
        self.flood_fill(coord)

        non_captured_tiles = []
        captured_tiles = []

        score = 0

        for tile in self.get_all_tiles():
            if not tile.captured:
                if tile.visited == True:
                    captured_tiles.append(tile)
                else:
                    non_captured_tiles.append(tile)
                tile.visited = False
        
        captured_len = len(captured_tiles)
        non_captured_len = len(non_captured_tiles)

        # if there is only oe captured and 1 non captured tile, then that means that those were the last 2 tiles.
        if captured_len == non_captured_len == 1:
            captured_tiles[0].captured = 1
            non_captured_tiles[0].captured = 1

            return {
                "outcome" : "end",
                "tiles" : captured_tiles,
                "tiles2" : non_captured_tiles
            }
            

        # We make sure that the amount of captured tiles isn't the same as the amount left in the game, which would mean that none got captured since all tiles are accessible
        if captured_len != len(self.tiles_left):
            score = min(captured_len, non_captured_len)

            # we only take away the smaller group of tiles
            if captured_len > non_captured_len:
                for tile in non_captured_tiles:
                    tile.captured = 1
                final_captured_tiles = non_captured_tiles
                final_non_captured_tiles = captured_tiles

            else:
                for tile in captured_tiles:
                    tile.captured = 1
                final_captured_tiles = captured_tiles
                final_non_captured_tiles = non_captured_tiles


            # The tiles not captured are now the tiles that remain
            self.tiles_left = final_non_captured_tiles

            return {
                "outcome" : "tiles captured",
                "tiles" : final_captured_tiles,
                "score" : score
            }
        #This means no tile was captured
        else:
            return {"outcome" : "nothing captured"}


    def make_move(self, coord, direction):
        """takes in address/coordinates and direction, adds a wall there and checks whether that wall cut off any square"""
        wall_placed_successfully = self.add_wall(coord, direction)

        if wall_placed_successfully:
            return self.apply_flood_fill(coord)
        else:
            return {"outcome" : "CouldNotAddWall"}

    def is_valid_position(self, addr):
        """returns whether the given address is in the grid bounds"""
        if addr != None:
            return 0 <= addr[0] <= self.width - 1 and 0 <= addr[1] <= self.height - 1

    def get_tile(self, pos):
        """returns the tile object for a given address, if the address is valid"""
        x, y = pos
        if self.is_valid_position(pos):
            return self.grid[y][x]
        
    def get_all_tiles(self):
        for row in self.grid:
            for tile in row:
                yield tile

    def direction_has_wall(self, tile, direction):
        return isinstance(tile.walls[direction], Border)
        

    def getSurroundingCoords(self, x, y):
        return (x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)

    def flood_fill(self, addr):
        tile = self.get_tile(addr)
        tile.visited = True

        self.player_turn_counter = 0
        x, y = addr

        n, e, s, w = self.getSurroundingCoords(x, y)
        
        for direction, coord in zip("nesw", (n, e, s, w)):
            next_tile = self.get_tile(coord)
            has_wall = self.direction_has_wall(tile, direction)
            
            # Check if next tile is valid and 
            if self.is_valid_position(coord) and not has_wall and not next_tile.visited and not next_tile.captured:
                self.flood_fill(coord)

    
    def print_board(self):
        def print_horizontal(row, bottom=False):
            print_row = ""
            for tile in row:
                tile_n = tile.walls["n"]
                if tile_n != None or bottom:
                    print_row += " ———"
                else:
                    print_row += "    "
            print(print_row)
            
        def print_vertical(row):
            print_row = "|"
            for tile in row:
                if tile.captured:
                    captured = tile.captured
                else:
                    captured = 0
                
                tile_e = tile.walls["e"]
                if tile_e != None:
                    print_row += f" {captured} |"
                else:
                    print_row += f" {captured}  "
            print(print_row)

        for row in self.grid:
            print_horizontal(row)
            print_vertical(row)
        print_horizontal(self.grid[-1], bottom=True)
        
    def __deepcopy__(self, memodict = {}):
        grid = Grid(self.width, self.height)
        grid.grid = deepcopy(self.grid)
        grid.tiles_left = deepcopy(self.tiles_left)
        return grid

class Game:
    def __init__(self, grid=(8, 8)):
        """takes an optional grid instance (in case one doesn't want 8x8)"""
        self.players = []
        self.players_dict = {}
        
        x, y = grid
        self.grid = Grid(x, y)
        self.grid.create_grid()

        self.player_turn_counter = 0
        self.numberOfPlayers = 0
        self.moves = []
        self.over = False

    def add_player(self, player):
        self.players.append(player)
        if self.numberOfPlayers == 0:
            self.current_player = player
        self.numberOfPlayers += 1

        self.players_dict[player.username] = player
        return player

    def remove_player(self, username):
        player = self.players_dict[username]

        self.players.remove(player)
        del self.players_dict[username]

        self.current_player = self.next_player()

    def next_player(self):
        return self.players[(self.player_turn_counter + 1) % len(self.players)]
        
    def play(self, data):
        """data: {
            player: username,
            wall: x-y-d
        }
        """


        self.moves.append(data)

        player = data["player"]
        wall_list = data['wall'].split("-")
        coord, direction = (int(wall_list[0]), int(wall_list[1])), wall_list[2]

        self.numberOfPlayers = len(self.players)

        if self.current_player.username == player:
            result = self.grid.make_move(coord, direction)

            if result["outcome"] == "CouldNotAddWall":
                # {"outcome" : "CouldNotAddWall"}
                return result

            outcome = result["outcome"]

            if outcome == "end":
                self.current_player.points += 1
                self.next_player().points += 1
                self.over = True


            elif outcome == "tiles captured":
                self.current_player.points += result["score"]
                result["total score"] = self.current_player.points


            self.current_player = self.next_player()
            self.player_turn_counter += 1

            return result
        else:
            print("It's not this player's turn:")
            print("    User that sent the message:", player)
            print("    User who's turn it is:", self.current_player.username)
            print("    List of players:", [player.username for player in self.players])
            return "InvalidTurn"
        
    def input_to_coords(self, name, number):
        entry = input(f"{name} ({number}): ")

        data = entry.split()
        try:
            # We get the x, y coordinates as well as the direction d
            x, y, d = data
            x, y = int(x) - 1, self.grid.height - int(y)
            if d not in ["n", "e", "s", "w"]:
                raise Exception
            return f"{x}-{y}-{d}"

        except Exception:
            print(f"The input is invalid: {entry}")
            return self.input_to_coords(name, number)
            
    def coords_to_input(self, x, y, d):
        """Turn game coordinates into easily readable coords:
        in 4xn:
        start:  top left (0,0)          bottom left (1,1)
                    0 0 e        -->        1 4 e 
                    0 3 n        -->        1 1 n
        """
        x, y = x + 1, self.grid.height - y
        return " ".join([str(x), str(y), d])


class Player:
    def __init__(self, game, username, colour):
        self.username = username
        self.grid = game.grid
        self.points = 0
        self.colour = colour
        self.number = len(game.players)
        self.game = game

class LocalPlayer(Player):
    def play(self):
        wall = self.game.input_to_coords(self.username, self.number)

        data = {
            "player" : self.username,
            "wall" : wall
        }
        start_time = time()
        result = self.game.play(data)
        print(f"Flood fill took {time() - start_time}s")
        if result["outcome"] == "CouldNotAddWall":
            print("Invalid Coords, couldn't add wall!")
            self.grid.print_board()
            self.play()

        return result


class PlayerAI(Player):
    def __init__(self, game, username, colour):
        Player.__init__(self, game, username, colour)
        self.calculations = 0

    def play(self):
        start_time = time()
        print(f"{self.username} ({self.number}): ", end="")
        game_copy = deepcopy(self.game)

        # odd number of depth is counter productive, since the AI will try to maximize it's gains, no matter what the opponent gets.
        # If the only way to get 1 tile is by giving the opponent half the board, the AI will do so.
        self.depth = round(  (   (len(self.game.moves) * 1.5) / self.grid.total_n_of_moves)) * 2 + 2

        result = self.Max_n_shallow(game_copy, self, floor(self.grid.width * self.grid.height / 2) + 1)

        wall = result["moves"][0]

        x = wall[0][0]
        y = wall[0][1]
        d = wall[1]

        wall = f"{x}-{y}-{d}"

        data = {
            "player" : self.username,
            "wall" : wall
        }

        print(self.game.coords_to_input(x, y, d))
        time_it_took = time() - start_time
        print(f"It took {time_it_took}s")

        print(self.calculations, "calculations")
        self.calculations = 0

        return self.game.play(data)

    def get_difference(self, scores, player):
        temp_dict = {k: scores[k] for k in scores.keys() - {player.username}}
        current_max_opponent_points = max(temp_dict.values())

        return scores[player.username] - current_max_opponent_points

    def Max_n_shallow(self, position, player, upper_bound, depth=None, _first_play=None):
        # if no depth is given, just use the default depth (because it's not possible to give a class variable as optional variable)
        if depth == None:
            depth = self.depth

        # our base case, in case the game is finished or the max depth has been reached
        if depth == 0 or position.over:
            player_scores = {player.username : player.points for player in position.players}

            self.calculations += 1
            return {"scores" : player_scores, "moves" : [_first_play]}

        area = self.grid.height * self.grid.width
        current_best = { "scores" : {player_iter.username : 0 if player_iter.username == player.username else area for player_iter in position.players}, "moves" : []}

        username = player.username
        

        for tile in position.grid.tiles_left:
            for direction in ["n", "e"]:
                if tile.walls[direction] == None:
                    new_position = deepcopy(position)

                    if depth == self.depth:
                        _first_play = ((tile.x, tile.y), direction)

                    data = {
                    "player" : username,
                    "wall" : f"{tile.x}-{tile.y}-{direction}"
                    }

                    new_position.play(data)
                    # new_position.grid.print_board()

                    if current_best["scores"][username] >= upper_bound:
                        return current_best

                    current = self.Max_n_shallow(new_position, new_position.current_player, upper_bound - current_best["scores"][username], depth - 1, _first_play)
                    # if current player's points are more than before, or if the current and best are the same points, minimize opponent's points
                    current_player_score = current["scores"][username]
                    current_best_player_score = current_best["scores"][username]

                    current_difference = self.get_difference(current["scores"], player)
                    best_difference = self.get_difference(current_best["scores"], player)

                    # check Ipad for improvement ideas
                    if current_difference > best_difference or (current_difference == best_difference and current_player_score > current_best_player_score):
                        current_best = current
                    elif current_difference == best_difference:
                        current_best["moves"].append(_first_play)

        return {"scores" : current_best["scores"], "moves" : [choice(current_best["moves"])]}
            
if __name__ == "__main__":
    def local_game():
        n = 8
        game = Game((n, n))

        player_1 = LocalPlayer(game, "Nathan", "red")
        player_2 = PlayerAI(game, "Max", "blue")
        player_3 = PlayerAI(game, "MaximilianMus", "black")

        game.add_player(player_2)
        game.add_player(player_1)
        # game.add_player(player_3)

        player_id = len(game.players)
            

        print("Give an input in the following format: 'x y direction'. x and y are coordinates, direction is either n/e/s/w")
        while True:
            print("Here is the current board:")
            game.grid.print_board()
            print("――――――――――――――――――――――――――――――――――――")

            player_rotation = game.player_turn_counter % player_id
            current_player = game.players[player_rotation]

            result = current_player.play()

            break
            
            if result["outcome"] == "end":
                game.grid.print_board()

                print("Here are the final results:")
                for player in game.players:
                    print(f"{player.username}: {player.points}")
                break


    #cProfile.run("local_game()")
    local_game()