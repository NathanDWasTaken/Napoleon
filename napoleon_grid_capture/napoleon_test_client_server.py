# pos is a coordinate in the form (x, y)
from copy import deepcopy, copy
from random import choice
from time import time
from math import floor
import numpy, ujson

import cProfile


# returns the variation of coordinate when going a certain direction
# east -> x + 1
variation_direction = {
    "n": (0, -1), (0, -1) : "n",
    "e": (1, 0), (1, 0) : "e",
    "s": (0, 1), (0, 1) : "s",
    "w": (-1, 0), (-1, 0) : "w"
}

def get_coord_of_2nd_tile(coord, direction):
    """do operation element wise between coord1 and coord2"""
    variation = variation_direction[direction]
    difference = []

    for element2, element1 in zip(variation, coord):
        difference.append(element2 + element1)

    return tuple(difference)

    
opposite_direction = {"n" : "s", "e" : "w", "s" : "n", "w" : "e"}

#————————————————————————————————————————————————
class CouldNotAddWall(Exception):
    pass

class InvalidInput(Exception):
    pass

class InvalidDirection(InvalidInput):
    pass

class InvalidTurn(Exception):
    pass


class Tile:
    def __init__(self, x, y):
        self.coords = (x, y)
        self.captured = False
        self.visited = False
        
        self.walls = {"n" : None, "e" : None, "s" : None, "w" : None}

    def __deepcopy__(self, memodict={}):
        tile = Tile(self.coords[0], self.coords[1])
        tile.captured = self.captured
        tile.walls = copy(self.walls)

        return tile


class Border:
    placed = True
    pass


class Wall(Border):
    def __init__(self, coord1, coord2):
        self.coords = (coord1, coord2)
        self.tiles = frozenset({coord1, coord2})
        self.placed = False

    def __deepcopy__(self, memodict={}):
        wall = Wall(self.coords[0], self.coords[1])
        wall.placed = self.placed
        return wall

class Grid:
    def __init__(self, width=8, height=8):
        if 1 < width and 1 < height:
            self.width, self.height = width, height
            self.grid = []
            self.tiles_left = []

            self.walls_left = {}
            
        else:
            print("Both grid dimensions have to be bigger than 1")

    def create_grid(self):
        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile = Tile(x, y)
                row.append(tile)
                self.tiles_left.append(tile)
            self.grid.append(row)
        
        for tile in self.get_all_tiles():
            for direction, check in {"n" : tile.coords[1] == 0, "e" : tile.coords[0] == self.width - 1, "s" : tile.coords[1] == self.height - 1, "w" : tile.coords[0] == 0}.items():
                if check:
                    tile.walls[direction] = Border()
                elif tile.walls[direction] == None:
                    coord1 = (tile.coords[0], tile.coords[1])
                    coord2 = get_coord_of_2nd_tile((tile.coords[0], tile.coords[1]), direction)

                    wall = Wall(coord1, coord2)

                    tile.walls[direction] = wall
                    tile2 = self.get_tile(coord2)
                    tile2.walls[opposite_direction[direction]] = wall
                    self.walls_left[frozenset({coord1, coord2})] = wall

        self.total_n_of_moves = self.height * (self.width - 1) + self.width * (self.height - 1)
        print(f"All possible first moves:", self.total_n_of_moves)

    def add_wall_using_direction(self, coord1, direction):
        """gets coords of tile 2 using coord1 and direction and calls add_wall"""
        # we can figure out coords of addr2 if we know addr1 and the direction it wants to go
        coord2 = get_coord_of_2nd_tile(coord1, direction)
        self.add_wall(coord1, coord2)


    def add_wall(self, coord1, coord2):
        """adds a wall to the tile object if it doesn't have one yet using the coords of 2 tiles"""

        tile1 = self.get_tile(coord1)
        tile2 = self.get_tile(coord2)

        if not (tile1.captured or tile2.captured):
            try:
                wall = self.walls_left.pop(frozenset({tile1.coords, tile2.coords}))
                wall.placed = True
            except KeyError:
                raise CouldNotAddWall()
        else:
            raise CouldNotAddWall()

    def apply_flood_fill(self, coord):
        self.flood_fill(coord)

        non_visited_tiles = []
        visited_tiles = []

        score = 0

        for tile in self.tiles_left:
            if tile.visited == True:
                visited_tiles.append(tile)
            else:
                non_visited_tiles.append(tile)
            tile.visited = False

        # if there is only oe captured and 1 non captured tile, then that means that those were the last 2 tiles.
        if len(visited_tiles) == len(non_visited_tiles) == 1:
            visited_tiles[0].captured = 1
            non_visited_tiles[0].captured = 1

            return {
                "outcome" : "end",
                "tiles" : visited_tiles,
                "tiles2" : non_visited_tiles
            }
            

        # We make sure that the amount of captured tiles isn't the same as the amount left in the game, which would mean that none got captured since all tiles are accessible
        if len(visited_tiles) != len(self.tiles_left):
            score = min(len(visited_tiles), len(non_visited_tiles))

            # we only take away the smaller group of tiles
            if len(visited_tiles) > len(non_visited_tiles):
                for tile in non_visited_tiles:
                    tile.captured = 1
                final_visited_tiles = non_visited_tiles
                self.tiles_left = visited_tiles


            else:
                for tile in visited_tiles:
                    tile.captured = 1
                final_visited_tiles = visited_tiles
                self.tiles_left = non_visited_tiles


            return {
                "outcome" : "tiles captured",
                "tiles" : final_visited_tiles,
                "score" : score
            }

        #This means no tile was captured
        else:
            return {"outcome" : "nothing captured"}

            

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
            has_wall = tile.walls[direction].placed
            
            # Check if next tile is valid and 
            if self.is_valid_position(coord) and not has_wall and not next_tile.visited and not next_tile.captured:
                self.flood_fill(coord)

    
    def print_board(self):
        def print_horizontal(row, bottom=False):
            print_row = ""
            for tile in row:
                tile_n = tile.walls["n"]
                if tile_n.placed or bottom:
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
                if tile_e.placed:
                    print_row += f" {captured} |"
                else:
                    print_row += f" {captured}  "
            print(print_row)

        for row in self.grid:
            print_horizontal(row)
            print_vertical(row)
        print_horizontal(self.grid[-1], bottom=True)
        
    def __deepcopy__(self, memodict={}):
        grid = Grid(self.width, self.height)
        grid.grid = deepcopy(self.grid)
        grid.tiles_left = deepcopy(self.tiles_left)
        grid.walls_left = deepcopy(self.walls_left)
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
        if self.players == []:
            self.current_player = player

        self.players.append(player)
        self.players_dict[player.username] = player
        return player

    def remove_player(self, username):
        player = self.players_dict[username]

        self.players.remove(player)
        del self.players_dict[username]

        self.current_player = self.players[self.player_turn_counter]

    def next_player(self):
        self.player_turn_counter = (self.player_turn_counter + 1) % len(self.players)
        return self.players[self.player_turn_counter]
        
    def play(self, player, coord1, coord2):
        if self.current_player.username == player:
            self.grid.add_wall(coord1, coord2)
            result = self.grid.apply_flood_fill(coord1)
            
            outcome = result["outcome"]

            if outcome == "end":
                self.current_player.points += 1
                self.next_player().points += 1
                self.over = True


            elif outcome == "tiles captured":
                self.current_player.points += result["score"]
                result["total score"] = self.current_player.points


            self.current_player = self.next_player()

            return result
        else:
            raise InvalidTurn

    def play_data(self, data):
        """data: {
            player: username,
            wall: x-y-d
        }
        """


        player = data["player"]
        wall_list = data['wall'].split("-")
        coord, direction = (int(wall_list[0]), int(wall_list[1])), wall_list[2]
        coord2 = get_coord_of_2nd_tile(coord, direction)

        if self.current_player.username == player:
            result = self.play(player, coord, coord2)
            self.moves.append(data)
            return result
        else:
            raise InvalidTurn


        
        
    def input_to_coords(self, name, number):
        entry = input(f"{name} ({number}): ")

        data = entry.split()
        try:
            # We get the x, y coordinates as well as the direction d
            x, y, d = data
            x, y = int(x) - 1, self.grid.height - int(y)
            if d not in ["n", "e", "s", "w"]:
                raise InvalidDirection()
            return f"{x}-{y}-{d}"

        except (InvalidDirection, ValueError):
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

        try:
            start_time = time()
            result = self.game.play_data(data)
            print(f"Flood fill took {time() - start_time}s")
            return result
        except CouldNotAddWall:
            print("Invalid Coords, couldn't add wall!")
            self.grid.print_board()
            return self.play()
        except InvalidTurn:
            print("It's not this player's turn")
            self.grid.print_board()
            return self.play()



class PlayerAI(Player):
    def __init__(self, game, username, colour):
        Player.__init__(self, game, username, colour)
        self.calculations = 0

    def play(self):
        start_time = time()
        print(f"{self.username} ({self.number}): ", end="")
        game_copy = deepcopy(self.game)

        # Calculates the depth the machine should use
        # odd number of depth is counter productive, since the AI will try to maximize it's gains, no matter what the opponent gets.
        # If the only way to get 1 tile is by giving the opponent half the board, the AI will do so.
        self.depth = round(((len(self.game.moves) * 1.5) / self.grid.total_n_of_moves)) * 2 + 2

        result = self.Max_n_shallow(game_copy, self, floor(self.grid.width * self.grid.height / 2) + 1)

        wall = result["moves"][0]

        tile1 = list(wall.tiles)[0]
        tile2 = list(wall.tiles)[1]

        difference = numpy.array(tile2) - numpy.array(tile1)
        x = tile1[0]
        y = tile1[1]
        d = variation_direction[tuple(difference)]

        data = {
            "player" : self.username,
            "wall" : f"{x}-{y}-{d}"
        }

        print(self.game.coords_to_input(x, y, d))
        time_it_took = time() - start_time
        print(f"It took {time_it_took}s")

        print(self.calculations, "calculations")
        self.calculations = 0

        return self.game.play_data(data)


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
        current_best = {"scores" : {player_iter.username : 0 if player_iter.username == player.username else area for player_iter in position.players}, "moves" : []}

        username = player.username

        for wall in position.grid.walls_left.values():
            new_position = deepcopy(position)

            if depth == self.depth:
                _first_play = wall

            tiles = list(wall.tiles)

            try:
                new_position.play(player.username, tiles[0], tiles[1])

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
            except CouldNotAddWall:
                continue

        return {"scores" : current_best["scores"], "moves" : [choice(current_best["moves"])]}
            
if __name__ == "__main__":
    def local_game():
        n = 8
        game = Game((n, n))

        player_1 = LocalPlayer(game, "Nathan", "red")
        player_2 = LocalPlayer(game, "Sarah", "blue")
        player_2 = PlayerAI(game, "Max", "blue")
        # player_3 = PlayerAI(game, "MaximilianMus", "black")

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

            
            if result["outcome"] == "end":
                game.grid.print_board()

                print("Here are the final results:")
                for player in game.players:
                    print(f"{player.username}: {player.points}")
                break



    #cProfile.run("local_game()")
    local_game()