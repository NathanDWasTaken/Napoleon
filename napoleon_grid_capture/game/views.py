from django.shortcuts import render, redirect
from django.http import HttpResponse
from uuid import uuid4

def create_uuid():
    uuid = str(uuid4())
    return uuid.replace("-", "_")

def multiplayer(request, game_id):
    return render(request, "game/grid_multiplayer.html", {'game_id' : game_id})

def local(request, game_id):
    return render(request, "game/grid_local.html", {'game_id' : game_id})

def local_redirect(request):
    return redirect(f"/game/local/{create_uuid()}/")

def game_selection(request):
    return redirect(f"{create_uuid()}/")
    # return render(request, "game/index.html")