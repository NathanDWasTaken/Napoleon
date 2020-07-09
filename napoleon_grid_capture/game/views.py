from django.shortcuts import render
from django.http import HttpResponse


def game(request, game_id):
    return render(request, "game/grid.html", {'game_id' : game_id})