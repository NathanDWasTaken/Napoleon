#include <iostream>
#include <vector>
using namespace std;


class Tile {
public:
    int x, y;

    bool captured, visited;

    Tile(int X, int Y) {
        x = X;
        y = Y;

        captured = false;
        visited = false;
    };
};


class Grid {
public:
    int width, height, no_tiles_left;

    Grid(int WIDTH, int HEIGHT) {
        width = WIDTH;
        height = HEIGHT;
        no_tiles_left = width * height;

        vector < vector < Tile > > tile_grid;

        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                Tile tile(x, y);

                tile_grid[x][y] = tile;
            }
        }
    }
};

//Shows the use of a Null pointer to represent "nothing".
int main() {
    Tile tile(0, 0);

    vector < vector < Tile > > vecTest;

    Tile tile1(0, 0);
    Tile tile2(0, 1);
    Tile tile3(0, 2);

    vector < Tile > row = {tile1, tile2, tile3};

}


int* create_array(int size) {
    int *arr = new int[size];

    for (int i = 0; i < size; i++) {
        arr[i] = i;
    }

    return arr;
}