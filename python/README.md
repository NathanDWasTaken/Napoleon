# Napoleon Grid Capture (Nagrica)

This repo serves as implementation of a game I used to play a lot in highschool, we called it Napoleon.


## Rules

This game works very similar to Dots and Boxes. It's a turn based game with two (or more) players. A player can, on their turn, draw a single horizontal/vertical line of length 1 on a grid.

If a drawn line separates a group of cells in the playing area into 2 distinct regions, the smallest of the 2 areas goes to the player who made the move. Each cell inside this area counts as one point. The larger area not captured by the player is the new playing area. 

The goal is to get as many points as possible. Points are scored by capturing cells.

As the game goes on, more and more cells will have been captured, while the playing area keeps shrinking.


## Features
- [X] Working Basics
- [X] Working AI
- [ ] Interactive Implemenations:
    - [X] CLI
    - [ ] Tkinter/Pygame
    - [ ] Website


## Personal Goals
- [X] Mostly fully implement logic myself (by hand)
- [ ] Optimize logic & game
- [ ] Create powerfull Computer opponents
- [ ] Recreate part or all of the code in another language (rust)




## Capture Detection

### Current Implementation

#### Directional-DFS

Currently we use a greedy DFS algorithm to determine whether 2 cells (ones on opposite sides of the wall) can be connected. If they can, then we know no area has been captured



### Possible Optimizations

#### DFS-MitM (Meet in the Middle)
With the current implementation, we can find connected cells (and thus non-captured tiles) in an open grid fairly quickly. In a closed grid (with imbalanced group sizes), there is a 50/50 chance we select the small area or the big one. A possible approach would be to run our algorithm from both sides, part of 2 different groups. If both groups meet, there is a connection. If one group is out of moves, they do not meet, and that group is the captured one

#### Online bridge detection

A bridge in Graph theory is an edge that connects 2 sets of nodes together. If a bridge is removed, a capture happens. We could try implementing an online bridge detection engine, which is able to dynamically update the bridge data upon edge deletion.


## Computer Adversary

TODO



## Game Names
- Partition
- Fault Lines
- Walled off
- Bonaparte
- Divide X Conquer
- Annex