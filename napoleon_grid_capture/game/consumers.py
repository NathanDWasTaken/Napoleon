import json
from channels.generic.websocket import WebsocketConsumer
from napoleon import Game, Grid


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.game = None

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
            
        data = json.loads(text_data)
        if self.game == None:
            grid = Grid(width=data["width"], height=data["height"])
            self.game = Game(grid=grid)
            return None
        wall = data['wall']
        self.game

        self.send(text_data=json.dumps({
            'player': '',
            'wall' : wall
        }))