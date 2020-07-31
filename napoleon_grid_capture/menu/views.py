from django.shortcuts import render
from uuid import uuid4


def menu(request):
    return render(request, "menu/menu.html",  {'game_id' : str(uuid4())})