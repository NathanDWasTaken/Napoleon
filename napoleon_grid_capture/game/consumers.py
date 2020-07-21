import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .napoleon import Game, Grid, Border

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = 'game_%s' % self.game_id

        # Join room group
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )

        try:
            self.channel_layer.game_groups
        except AttributeError:
            self.channel_layer.game_groups = {}


        await self.accept()



    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )

    def get_game(self):
        return self.channel_layer.game_groups[self.game_id]

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.pop("command")

        if command == "make_move":
            game = self.get_game()
            result = game.play(data)

            remove_walls = None

            if result == None:
                tiles = None
            else:
                if result["score"] == None:
                    #this means that the last 2 tiles were captured (you can get these by calling "tiles" and "tiles2")
                    pass
                tiles = [f"{tile.x}-{tile.y}" for tile in result["tiles"]]
                remove_walls = []
                for tile in result["tiles"]:
                    for direction in ["s", "e"]:
                        wall = tile.walls[direction]
                        if not isinstance(wall, Border):
                            remove_walls.append(f"{tile.x}-{tile.y}-{direction}")

            move = {
                'player': data["player"],
                'tiles' : tiles,
                'wall' : data['wall'],
                'remove_walls' : remove_walls
            }

            # Send message to room group
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'send_move',
                    'move': move
                }
            )

        elif command == "create_game":
            try:
                game = self.get_game()

                for move in game.moves:
                    await self.send(text_data=json.dumps(move))
            except KeyError:
                grid = Grid(width=data["width"], height=data["height"])
                game = Game(grid=grid)
                self.channel_layer.game_groups[self.game_id] = game

                game.add_player(data["player"])


    # Sendf message to member in group
    async def send_move(self, event):
        move = event['move']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(move))