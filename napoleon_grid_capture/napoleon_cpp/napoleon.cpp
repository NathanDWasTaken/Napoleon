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

class Player {
public:
    int score = 0;


    string username;
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
    Grid grid(6, 6);

    cout << "test" << endl;
}
