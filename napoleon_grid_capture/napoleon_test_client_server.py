# pos is a coordinate in the form (x, y)
from copy import deepcopy


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
        self.value = 0
        self.x = x
        self.y = y
        self.captured = False
        self.visited = False
        
        self.walls = {"n" : None, "e" : None, "s" : None, "w" : None}


class Border:
    pass


class Wall(Border):
    def __init__(self, tile1, tile2):
        self.tiles = [tile1, tile2]


class Grid:
    def __init__(self, width=8, height=8):
        if 1 < width and 1 < height:
            self.width, self.height = width, height
            self.no_total_tiles = width * height
            self.no_tiles_left = self.no_total_tiles
            self.grid = []
            self.tiles_left = []

            for y in range(height):
                row = []
                for x in range(width):
                    tile = Tile(x, y)

                    if y == 0:
                        tile.walls["n"] = Border()
                    if x == width - 1:
                        tile.walls["e"] = Border()
                    if y == height - 1:
                        tile.walls["s"] = Border()
                    if x == 0:
                        tile.walls["w"] = Border()

                    self.tiles_left.append(tile)
                    row.append(tile)
                self.grid.append(row)

        else:
            print("Both grid dimensions have to be bigger than 1")

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

        if tile1.walls[direction] == tile2.walls[opposite_direction[direction]] == None:
            wall = Wall(tile1, tile2)
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
        
        captured_len = len(captured_tiles)
        non_captured_len = len(non_captured_tiles)


        if captured_len == non_captured_len == 1:
            captured_tiles[0].captured = 1
            non_captured_tiles[0].captured = 1

            return {
                "outcome" : "end",
                "tiles" : captured_tiles,
                "tiles2" : non_captured_tiles
            }

        for tile in self.get_all_tiles():
            tile.visited = False

        # We make sure that the amount of captured tiles isn't the same as the amount left in the game, which would mean that none got captured since all tiles are accessible
        if captured_len != self.no_tiles_left:
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



            self.no_tiles_left -= score
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
        


class Game:
    def __init__(self, grid=(8, 8)):
        """takes an optional grid instance (in case one doesn't want 8x8)"""
        self.players = []
        self.players_dict = {}
        
        x, y = grid
        self.grid = Grid(x, y)

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
        result = self.game.play(data)
        if result["outcome"] == "CouldNotAddWall":
            print("Invalid Coords, couldn't add wall!")
            self.play()

        return result


class PlayerAI(Player):
    def __init__(self, game, username, colour, depth=3):
        Player.__init__(self, game, username, colour)
        self.max_depth = depth

        self.default_depth = 2

    def play(self):
        # coords, direction = self.Max_n_shallow(deepcopy(self.game), self, self.game.grid.no_total_tiles, self.max_depth)[1]

        # data = {
        #     "player" : self.username,
        #     "wall" : f"{coords[0]}-{coords[1]}-{direction}"
        # }

        # return self.game.play(data)



        game_copy = deepcopy(self.game)
        result = self.Max_n(game_copy, self)
        wall = result[1]

        wall = f"{wall[0][0]}-{wall[0][1]}-{wall[1]}"

        data = {
            "player" : self.username,
            "wall" : wall
        }

        return self.game.play(data)



        # print(self.minimax(deepcopy(self.game), 3, False))

    def minimax(self, position, depth, maximizingPlayer, alpha=float("-inf"), beta=float("+inf")):
        if depth == 0 or position.over:
            return position.current_player.points - position.next_player().points

        if maximizingPlayer:
            maxEval = float("-inf")
            for tile in position.grid.tiles_left:
                for direction in ["n", "e"]:
                    # If there is no wall at the spot
                    if tile.walls[direction] == None:
                        game_copy = deepcopy(position)

                        data = {
                        "player" : game_copy.current_player.username,
                        "wall" : f"{tile.x}-{tile.y}-{direction}"
                        }

                        game_copy.play(data)

                        eval = self.minimax(game_copy, depth - 1, False, alpha, beta)
                        maxEval = max(maxEval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break

            return maxEval

        else:
            minEval = float("+inf")
            for tile in position.grid.tiles_left:
                for direction in ["n", "e"]:
                    # If there is no wall at the spot
                    if tile.walls[direction] == None:
                        game_copy = deepcopy(position)

                        data = {
                        "player" : game_copy.current_player.username,
                        "wall" : f"{tile.x}-{tile.y}-{direction}"
                        }

                        game_copy.play(data)

                        eval = self.minimax(game_copy, depth - 1, True, alpha, beta)
                        minEval = min(minEval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
            return minEval


    def Max_n(self, position, player, depth=None, _first_play=None):
        # if no depth is given, just use the default depth (because it's not possible to give a class variable as optional variable)
        if depth == None:
            depth = self.default_depth

        # our base case, in case the game is finished or 
        if depth == 0 or position.over:
            # position.grid.print_board()
            player_scores = {player.username : player.points for player in position.players}
            return player_scores, _first_play

        current_best = [{player.username : -1 for player in position.players}, None]


        for tile in position.grid.tiles_left:
            for direction in ["n", "e"]:
                if tile.walls[direction] == None:
                    new_position = deepcopy(position)

                    if depth == self.default_depth:
                        _first_play = ((tile.x, tile.y), direction)

                    data = {
                    "player" : player.username,
                    "wall" : f"{tile.x}-{tile.y}-{direction}"
                    }

                    new_position.play(data)
                    # new_position.grid.print_board()

                    current = self.Max_n(new_position, new_position.current_player, depth - 1, _first_play)
                    # if current player's points are more than before, or if the current and best are the same points, minimize opponent's points
                    current_player_score = current[0][player.username]
                    current_best_player_score = current_best[0][player.username]

                    opponents_current_sum = sum(current[0].values()) - current_player_score
                    opponents_best_sum = sum(current_best[0].values()) - current_best_player_score

                    if current_player_score > current_best_player_score or (current_player_score == current_best_player_score and opponents_current_sum < opponents_best_sum):
                        current_best = current

        return current_best


    def Max_n_shallow(self, position, player, upper_bound, depth=3, _initial_play=None):
        """position -> instance of Game, player -> instance of Player, upper_bound -> max amount of points someone could get (all tiles), depth -> how deep the algorithm goes"""
        if depth == 0 or position.over:
            #position.grid.print_board()
            return [player.points for player in position.players], _initial_play
        tiles_left = position.grid.tiles_left
        
        current_best = [[0] * len(position.players), None]

        # For each child
        for tile in tiles_left:
            for direction in ["n", "e"]:
                wall = tile.walls[direction]
                if wall == None:
                    game_copy = deepcopy(position)

                    if depth == self.max_depth:
                        _initial_play = ((tile.x, tile.y), direction)

                    data = {
                    "player" : player.username,
                    "wall" : f"{tile.x}-{tile.y}-{direction}"
                    }

                    result = game_copy.play(data)

                    #print("    " * (3 - depth) + f"{player.number} Trying:", data["wall"])
                    # game_copy.grid.print_board()

                    # If child is first child
                    if current_best[0][player.number] >= upper_bound:
                        return current_best
                    current = self.Max_n_shallow(game_copy, game_copy.current_player, upper_bound - current_best[0][player.number], depth - 1, _initial_play)
                    if current[0][player.number] > current_best[0][player.number]:
                        current_best = current
        return current_best

            
if __name__ == "__main__":
    def local_game():
        n = 4
        game = Game((n, n))

        player_1 = LocalPlayer(game, "Nathan", "red")
        player_2 = PlayerAI(game, "Max", "blue")

        game.add_player(player_1)
        game.add_player(player_2)

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



    local_game()