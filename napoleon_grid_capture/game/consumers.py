import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .napoleon import Game, Grid, Border

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']

        # Join room group
        await self.channel_layer.group_add(
            self.game_id,
            self.channel_name
        )
        self.lobby_leader = False

        default_group = {"game_inst" : None, "players" : {}, "started" : False}

        try:
            self.group = self.get_group()
        except AttributeError:
            self.channel_layer.game_groups = {self.game_id : default_group}
        except KeyError:
            self.channel_layer.game_groups[self.game_id] = default_group
        self.group = self.get_group()

        self.score = 0

        await self.accept()

    
    def get_group(self):
        return self.channel_layer.game_groups[self.game_id]

    
    # Send message to member in group
    async def send_move(self, event):
        move = event['move']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(move))


















class MultiplayerConsumer(GameConsumer):
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )

        self.group["players"].pop(self.username)

        if self.group["players"] == {}:
            self.channel_layer.game_groups.pop(self.game_id)

        if self.channel_layer.game_groups == {}:
            delattr(self.channel_layer, "game_groups")

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.pop("command")

        if command == "make move":
            remove_walls = None

            game_inst = self.group["game_inst"]

            result = game_inst.play(data)

            if result == "InvalidTurn":
                return

            elif result == None:
                tiles = None

            else:
                self.score = result["total score"]

                if result["outcome"] == "end":
                    #this means that the last 2 tiles were captured (you can get these by calling "tiles" and "tiles2")
                    pass
        
                else:
                    tiles = [f"{tile.x}-{tile.y}" for tile in result["tiles"]]
                    remove_walls = []
                    for tile in result["tiles"]:
                        for direction in ["s", "e"]:
                            wall = tile.walls[direction]
                            if not isinstance(wall, Border):
                                remove_walls.append(f"{tile.x}-{tile.y}-{direction}")

            move = {
                'command' : "add move",
                'score' : self.score,
                'player': self.username,
                'colour' : self.colour,
                'tiles' : tiles,
                'wall' : data['wall'],
                'remove_walls' : remove_walls
            }

            game_inst.moves.append(move)

            # Send message to room group
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type': 'send_move',
                    'move': move
                }
            )

        elif command == "join":
            self.group = self.get_group()
            self.username = data["player"]
            self.colour = data["colour"]

            if (game_inst := self.group["game_inst"]) != None:
                if not self.group["started"]:
                    self.group["players"][self.username] = self
                    
                    game_inst.add_player(self.username)

                for move in game_inst.moves:
                    await self.send(text_data=json.dumps(move))
            else:
                if not self.group["started"]:
                    grid = Grid(width=data["width"], height=data["height"])
                    game = Game(grid=grid)
                    game.add_player(self.username)
                    self.group["game_inst"] = game
                    
                    self.lobby_leader = True
                else:
                    print("Game already started, adding to spectators")

                self.group["players"][self.username] = self
                await self.send(text_data=json.dumps({
                    "command" : "join response",
                    "lobby leader" : self.lobby_leader
                    }))

        elif command == "start":
            if self.lobby_leader:
                await self.send(text_data=json.dumps({
                    "command" : "start response",
                    "player turn" : True
                    }))
                self.group["started"] = True
            else:
                print(f"Sorry but {self.username} can't start the game")

        else:
            print(command)












































class LocalConsumer(GameConsumer):
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )

        self.channel_layer.game_groups.pop(self.game_id)

        if self.channel_layer.game_groups == {}:
            delattr(self.channel_layer, "game_groups")

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.pop("command")

        if command == "make move":
            remove_walls = None

            game_inst = self.group["game_inst"]

            result = game_inst.play(data)


            player_name = data["player"]
            player_inst = game_inst.players_dict[player_name]

            if result == "InvalidTurn":
                return
            elif result == None:
                tiles = None
            else:
                if result["outcome"] == "end":
                    #this means that the last 2 tiles were captured (you can get these by calling "tiles" and "tiles2")

                    tile1 = result["tiles"][0]
                    tile1_id = f"{tile1.x}-{tile1.y}"

                    move1 = {
                        'score' : player_inst.points,
                        'player' : player_name,
                        'colour' : data["colour"],
                        'tiles' : [tile1_id],
                        'wall' : data['wall'],
                        'remove_walls' : [data["wall"]]
                    }

                    tile2 = result["tiles2"][0]
                    tile2_id = f"{tile2.x}-{tile2.y}"

                    next_player_name = data["next player"]

                    move2 = {
                        'score' : game_inst.players_dict[next_player_name].points,
                        'player' : next_player_name,
                        'colour' : data["next colour"],
                        'tiles' : [tile2_id],
                        'wall' : None,
                        'remove_walls' : None
                    }

                    for move in [move1, move2]:
                        await self.send(text_data=json.dumps(move))
                    return

                else:
                    tiles = [f"{tile.x}-{tile.y}" for tile in result["tiles"]]
                    remove_walls = []
                    for tile in result["tiles"]:
                        for direction in ["s", "e"]:
                            wall = tile.walls[direction]
                            if not isinstance(wall, Border):
                                remove_walls.append(f"{tile.x}-{tile.y}-{direction}")

            move = {
                'score' : player_inst.points,
                'player': player_name,
                'colour' : data["colour"],
                'tiles' : tiles,
                'wall' : data['wall'],
                'remove_walls' : remove_walls
            }

            game_inst.moves.append(move)

            # Send message to room group
            await self.send(text_data=json.dumps(move))

        elif command == "join":
            self.group = self.get_group()
            self.players = data["players"]

            # if game inst already exists
            if (game_inst := self.group["game_inst"]) != None:
                for move in game_inst.moves:
                    await self.send(text_data=json.dumps(move))
            
            # if game hasn't started
            elif not self.group["started"]:
                grid = Grid(width=data["width"], height=data["height"])
                game_inst = Game(grid=grid)
                self.group["game_inst"] = game_inst

            for player in self.players:
                game_inst.add_player(player["username"])