![Graphical output example](./images/headban.png)

# SantorinAI
AI Player tester for the Santorini game

## How to use
### 1. Install

With pip:
```bash
pip install --upgrade santorinai
```

You can also clone the repository and install it manually:
```bash
git clone https://github.com/Tomansion/SantorinAI.git
cd SantorinAI
pip install -r requirements.txt
```

### 2. Create a player

Create an override of the `Player` class in the `santorinai.player.py` file.

```python
from santorinai.player import Player

class MyPlayer(Player):
    """
    My player description
    """

    def name(self):
        return "My player name"

    # Placement of the pawns
    def place_pawn(self, board, pawn):
        my_pawn_number = pawn.number # Between 1 and 6 depending on the game mode
        my_player_number = pawn.player_number # Between 1 and 3 depending on the game mode

        # Do some magic here to choose a position
        my_choice = (2, 3) # A position on the 5x5 board

        return my_choice

    # Movement and building
    def play_move(self, board, pawn):
        my_initial_position = pawn.pos

        board_array = board.board # A 5x5 array of integers representing the board
        # 0: empty
        # 1: tower level 1
        # 2: tower level 2
        # 3: tower level 3
        # 4: terminated tower

        # Do some magic here to choose a position
        my_move_vector = (1, 1) # Moving top right
        my_build_vector = (1, 0) # Building right (relative to the new position)

        return my_move_vector, my_build_vector
```

Check our random players example in [our player examples folder](./santorinai/player_examples/)  to help you create your own.

### 3. Test your player

```python
from santorinai.tester import Tester
from santorinai.player_examples.random_player import RandomPlayer
from my_player import MyPlayer

# Init the tester
tester = Tester()
tester.verbose_level = 2 # 0: no output, 1: Each game results, 2: Each move summary
tester.delay_between_moves = 0.1 # Delay between each move in seconds
tester.display_board = True # Display a graphical view of the board in a window

# Init the players
my_player = MyPlayer()
random_payer = RandomPlayer()

# Play 100 games
tester.play_1v1(player1, player2, nb_games=100)
```
Output example:
```
Results:
Player Randy Random won 10 times
Player My player won 70 times
```
Graphical output example:
![Graphical output example](./images/board_image.png)

## Board utilities
We provide some utilities to help you manipulate the board.

```python
# Game informations
board.nb_players # Number of players in the game (2 or 3)
board.nb_pawns # Number of pawns (4 or 6) depending on the game mode
board.pawn_turn # Pawn that is currently playing
board.turn_number # Number of turn played since the beginning of the game

# Pawns
board_pawns = board.pawns # The other pawns on the board
pawn = board_pawns[0] # The first pawn on the board
pawn.pos # The position a pawn on the board (x, y), or (None, None) if it is not placed yet
pawn.number # The number of the  pawn on the board (between 1 and 6) depending on the game mode
pawn.player_number # The number of the player owning the pawn (between 1 and 3) depending on the game mode
playing_pawn = board.get_playing_pawn() # The pawn that is currently playing


# Board
board_array = board.board # A 5x5 array of integers representing the board
# 0: empty
# 1: tower level 1
# 2: tower level 2
# 3: tower level 3
# 4: terminated tower

# Movements
available_move_positions = board.get_possible_movement_positions(pawn)
available_build_positions = board.get_possible_building_positions(pawn)

# Board control
board.place_pawn(pos) # Place the current playing pawn on the board
board.play_move(move_vector, build_vector) # Play a move (move and build) with the current playing pawn

# Other
board.is_vector_valid(vector)
board.is_move_possible(start_pos, end_pos)
board.is_position_within_board(pos)
board.is_position_adjacent(pos1, pos2)
board.is_pawn_on_position(pos)
board.is_build_possible(builder_pos, build_pos)
board.copy() # Create a copy of the board, useful to test moves
print(board) # Print the board
```

## Credits

Creator of Santorini: [Roxley Games](https://roxley.com/)

Board 2D Gui library: [PySimpleGUI](https://www.pysimplegui.org/en/latest/)
