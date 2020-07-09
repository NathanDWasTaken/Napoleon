from django.shortcuts import render
from django.http import HttpResponse


def menu(request):
    return render(request, "game/menu.html")

def game(request):
    return render(request, "game/grid.html")