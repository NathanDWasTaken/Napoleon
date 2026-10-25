# Napoleon Grid Capture (Nagrica)

An implementation of a game I used to play in high school.

## How to play

A turn-based game for two (or more) players, similar to Dots and Boxes. On their turn, a player draws a single line of length 1 on a square grid. If that line splits the playing area into two separate regions, the player captures the smaller one and scores a point per captured cell. The larger region becomes the new playing area. The player with the most points wins.

## Repository layout

| Folder              | Contents                                  |
| ------------------- | ----------------------------------------- |
| [python/](python/)  | Python implementation (engine, CLI, tests) |

## History

The original 2020–2021 Django version (with the C++ experiment and TypeScript frontend) lives on the [`legacy`](../../tree/legacy) branch.
