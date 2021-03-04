# pos is a coordinate in the form (x, y)
from copy import deepcopy, copy
from random import choice
from time import time
from math import floor

import cProfile, ujson



class InvalidTurn(Exception):
    pass


# east -> x + 1 | x + 1 -> east
variation_direction = {
    "n": (0, -1), (0, -1): "n", 
    "e": (1, 0), (1, 0): "e", 
    "s": (0, 1), (0, 1): "s", 
    "w": (-1, 0), (-1, 0): "w"
}

# Inaccurate name, I know.
def get_coord_using_difference(coord1, coord2, operation="+"):
    """comparable to applying a vector to a point in geometry. 
    We use the starting point and the displacement (found in variation_direction) to get the second point (coord)"""
    difference = []

    for element2, element1 in zip(coord2, coord1):
        if operation == "+":
            result = element2 + element1
        elif operation == "-":
            result = element2 - element1

        difference.append(result)

    return tuple(difference)
# returns either:
# - the variation of coordinate when going a certain direction
# - the direction for a certain variation in coords

def get_coord_using_direction(coord, direction):
    return get_coord_using_difference(coord, variation_direction[direction])


    
opposite_direction = {"n" : "s", "e" : "w", "s" : "n", "w" : "e"}

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.captured = False
        self.visited_flood_fill = False
        self.visited_AI = False
        
        self.walls = {"n" : None, "e" : None, "s" : None, "w" : None}

    def __deepcopy__(self, memodict={}):
        tile = Tile(self.x, self.y)
        tile.captured = self.captured
        tile.visited_flood_fill = self.visited_flood_fill

        tile.walls = copy(self.walls)

        return tile

class Wall:
    pass

class Border(Wall):
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

        if not self.is_valid_coord(coord1):
            print("Address 1 is invalid:", coord1)
            return False

        coord2 = get_coord_using_direction(coord1, direction)

        if not self.is_valid_coord(coord2):
            print("Address 2 is invalid:", coord2)
            return False

        tile1 = self.get_tile(coord1)
        tile2 = self.get_tile(coord2)

        if not (tile1.captured or tile2.captured) and tile1.walls[direction] == tile2.walls[opposite_direction[direction]] == None:
            wall = Wall()
            tile1.walls[direction] = wall
            tile2.walls[opposite_direction[direction]] = wall

            return True

        return False

    def apply_flood_fill(self, coord, player_number):
        self.flood_fill(coord)

        non_captured_tiles = []
        captured_tiles = []

        score = 0

        for tile in self.get_all_tiles():
            if not tile.captured:
                if tile.visited_flood_fill == True:
                    captured_tiles.append(tile)
                else:
                    non_captured_tiles.append(tile)
                tile.visited_flood_fill = False
        
        captured_len = len(captured_tiles)
        non_captured_len = len(non_captured_tiles)

        # if there is only oe captured and 1 non captured tile, then that means that those were the last 2 tiles.
        if captured_len == non_captured_len == 1:
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
                final_captured_tiles = non_captured_tiles
                final_non_captured_tiles = captured_tiles

            else:
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


    def is_valid_coord(self, addr):
        """returns whether the given address is in the grid bounds"""
        if addr != None:
            return 0 <= addr[0] <= self.width - 1 and 0 <= addr[1] <= self.height - 1

    def get_tile(self, coord):
        """returns the tile object for a given address, if the address is valid"""
        x, y = coord
        if self.is_valid_coord(coord):
            return self.grid[y][x]
        
    def get_all_tiles(self):
        for row in self.grid:
            for tile in row:
                yield tile

    def direction_has_wall(self, tile, direction):
        return isinstance(tile.walls[direction], Wall)
        

    def getSurroundingCoords(self, x, y):
        return (x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)

    def flood_fill(self, addr):
        tile = self.get_tile(addr)
        tile.visited_flood_fill = True

        self.player_turn_counter = 0
        x, y = addr

        n, e, s, w = self.getSurroundingCoords(x, y)
        
        for direction, coord in zip("nesw", (n, e, s, w)):
            next_tile = self.get_tile(coord)
            has_wall = self.direction_has_wall(tile, direction)
            
            # Check if next tile is valid and 
            if self.is_valid_coord(coord) and not has_wall and not next_tile.visited_flood_fill and not next_tile.captured:
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
        self.moves = []
        self.over = False

    def add_player(self, player):
        if len(self.players) == 0:
            self.current_player = player
        self.players.append(player)
        player.number = len(self.players)

        self.players_dict[player.username] = player
        return player

    def remove_player(self, username):
        player = self.players_dict[username]

        self.players.remove(player)
        del self.players_dict[username]

        self.current_player = self.next_player()

    def next_player(self):
        return self.players[(self.player_turn_counter + 1) % len(self.players)]
        

    def play_data(self, data):
        """data: {
            player: username,
            wall: x-y-d
        }
        """


        player = data["player"]
        wall_list = data['wall'].split("-")
        coord, direction = (int(wall_list[0]), int(wall_list[1])), wall_list[2]
        coord2 = get_coord_using_difference(coord, direction)

        if self.current_player.username == player:
            result = self.make_move(player, coord, coord2)
            return result
        else:
            raise InvalidTurn


    def make_move(self, username, coord, direction):
        if self.current_player.username == username:
            self.moves.append([coord, direction])

            if not self.grid.add_wall(coord, direction):
                return {"outcome" : "CouldNotAddWall"}

            result = self.grid.apply_flood_fill(coord, self.current_player.number)

            if result["outcome"] == "CouldNotAddWall":
                # {"outcome" : "CouldNotAddWall"}
                return result

            outcome = result["outcome"]

            if outcome == "end":
                self.current_player.points += 1
                result["tiles"][0].captured = self.current_player.number

                next_player = self.next_player()
                next_player.points += 1
                result["tiles2"][0].captured = next_player.number

                self.over = True


            elif outcome == "tiles captured":
                for tile in result["tiles"]:
                    tile.captured = self.current_player.number

                self.current_player.points += result["score"]
                result["total score"] = self.current_player.points


            self.current_player = self.next_player()
            self.player_turn_counter += 1

            return result
        else:
            print("It's not this player's turn:")
            print("    User that sent the message:", username)
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
            return (x, y), d

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
        coords, direction = self.game.input_to_coords(self.username, self.number)

        start_time = time()
        result = self.game.make_move(self.username, coords, direction)

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
        game_copy = deepcopy(self.game)

        # ------ calculate the amount of moves left ------

        # iterate through each uncaptured tile in the game and check how many lack walls
        moves_this_turn = 0
        for tile in self.grid.tiles_left:
            for direction in ["n", "e"]:
                if tile.walls[direction] == None:
                    moves_this_turn += 1

        print("Max amount of moves left:", moves_this_turn)

        def get_n_of_moves_for_depth(n_of_initial_moves, depth_used):
            """returns the amount of moves that will have to be checked for a depth.
            For example if the bot can do 112 moves in one turn, then he will have to check 12432 moves for depth 2 (112 * 111)
            n_of_initial_moves is the amount of moves the bot can do the current move"""
            total_moves = n_of_initial_moves

            while depth_used > 1:
                n_of_initial_moves -= 1
                depth_used -= 1
                if n_of_initial_moves < 1:
                    break
                total_moves *= n_of_initial_moves


            return total_moves

        # Calculate the depth we can go while staying under the max_moves limit, the more moves to calculate the longer it takes
        depth = 2
        max_moves = 250000
        current_moves = 0
        while depth < 15:
            current_moves = get_n_of_moves_for_depth(moves_this_turn, depth + 1)
            if current_moves < max_moves:
                depth += 1
            else:
                break
        
        print("Current depth being used:", depth, f"(estimated moves to calculate: {get_n_of_moves_for_depth(moves_this_turn, depth)})")
        print(f"{self.username} ({self.number}): ", end="")

        self.depth = depth

        result = self.Max_n_shallow(game_copy, self, floor(self.grid.width * self.grid.height / 2) + 1)

        wall = result["moves"][0]

        x = wall[0][0]
        y = wall[0][1]
        d = wall[1]


        print(self.game.coords_to_input(x, y, d))
        time_it_took = time() - start_time
        print(f"It took {time_it_took}s")

        print(self.calculations, "calculations")
        self.calculations = 0

        return self.game.make_move(self.username, (x, y), d)

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

            
            return {"scores" : player_scores, "moves" : [_first_play]}

        area = self.grid.height * self.grid.width
        current_best = { "scores" : {player_iter.username : 0 if player_iter.username == player.username else area for player_iter in position.players}, "moves" : []}

        username = player.username
        
        # top depth is the surface or highest depth. Basically when it's the first time the function was called
        top_depth = depth == self.depth


        # If depth is not 1, then we only check each possible move at tiles where someone has already played, this saves huge amounts of calculations, since we don't check for every single possible move 
        # If depth is 1 then we loop through each still available move, since we don't want to limit the AI to only play moves on tiles that have already been played

        # Could still be heaviliy optimised -> currently each direction for a tile is tried, this means that some walls can and are calculated twice
        # This method does lead to AI making mistakes sometimes (when the move that would capture the group is on the edge, see ipad)
        # solution -> add direct neighbours to tiles list as well
        tiles = []
        if not top_depth:
            directions = ["n", "e", "s", "w"]
            # get tiles surrounding moves
            for coord, direction in position.moves:
                tile1 = self.grid.get_tile(coord)
                tile2 = self.grid.get_tile(get_coord_using_direction(coord, direction))

                for tile in (tile1, tile2):
                    if not tile.visited_AI and not tile.captured:
                        tiles.append(tile)
                        tile.visited_AI = True
        else:
            tiles = self.grid.tiles_left
            directions = ["n", "e"]



        for tile in tiles:
            tile.visited_AI = False
            for direction in directions:
                if tile.walls[direction] == None:
                    self.calculations += 1
                    new_position = deepcopy(position)

                    if top_depth:
                        _first_play = ((tile.x, tile.y), direction)


                    new_position.make_move(username, (tile.x, tile.y), direction)
                    # new_position.grid.print_board()

                    if current_best["scores"][username] >= upper_bound:
                        return current_best

                    current = self.Max_n_shallow(new_position, new_position.current_player, upper_bound - current_best["scores"][username], depth - 1, _first_play)
                    # if current player's points are more than before, or if the current and best are the same points, minimize opponent's points
                    current_player_score = current["scores"][username]
                    current_best_player_score = current_best["scores"][username]

                    current_difference = self.get_difference(current["scores"], player)
                    best_difference = self.get_difference(current_best["scores"], player)

                    if current_difference > best_difference or (current_difference == best_difference and current_player_score > current_best_player_score):
                        current_best = current
                    elif current_difference == best_difference:
                        current_best["moves"].append(_first_play)

        return {"scores" : current_best["scores"], "moves" : [choice(current_best["moves"])]}
            
if __name__ == "__main__":
    def local_game():
        n = 3
        game = Game((n, n))

        player_1 = LocalPlayer(game, "Nathan", "red")
        player_2 = PlayerAI(game, "Max", "blue")
        player_3 = PlayerAI(game, "MaximilianMus", "black")

        game.add_player(player_2)
        game.add_player(player_3)
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
                    print(f"{player.username} ({player.number}): {player.points}")
                break


    #cProfile.run("local_game()")
    local_game()