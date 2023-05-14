from santorinai.pawn import Pawn
from typing import Tuple


class Board:
    """
    Represents the game board for the Santorini game.

    Attributes:
        pawns (list): A list of pawn objects representing the pawns on the board.
        board_size (int): The size of the square game board.
        board (list): A 2D list representing the current state of the board.
        pawn_turn (int): The index of the current player's turn.
        winner_player_number (int): The player number of the winning player, if any.

    Board values:
        A 5x5 2D list representing the current state of the board:
        - 0: Empty space
        - 1: Tower level 1
        - 2: Tower level 2
        - 3: Tower level 3
        - 4: Terminated tower

    Methods:
        <list of methods>

    """

    def __init__(self, number_of_players: int):
        """
        Initializes a new instance of the Board class.

        Args:
            number_of_players (int): The number of players in the game.
        """

        # Create the pawns for each player
        self.pawns = []
        self.nb_players = number_of_players
        self.nb_pawns = number_of_players * 2

        # For 2 player games:
        # - Player 1 has pawns 1, 3
        # - Player 2 has pawns 2, 4

        # For 3 player games:
        # - Player 1 has pawns 1, 4
        # - Player 2 has pawns 2, 5
        # - Player 3 has pawns 3, 6

        for pawn_number in range(1, self.nb_pawns + 1):
            player_number = (pawn_number - 1) % number_of_players + 1
            self.pawns.append(Pawn(pawn_number, player_number))

        # Initialize the board
        self.board_size = 5
        self.board = [
            [0 for _ in range(self.board_size)] for _ in range(self.board_size)
        ]

        # Board values:
        # 0 = empty
        # 1 = tower level 1
        # 2 = tower level 2
        # 3 = tower level 3
        # 4 = terminated tower

        # Other board values:
        self.pawn_turn = 1
        self.winner_player_number = None
        self.turn_number = 1

    def is_move_possible(
        self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]
    ) -> Tuple[bool, str]:
        """
        Checks if a move from the start position to the end position is possible.

        Args:
            start_pos (tuple): The starting position [x, y] of the pawn.
            end_pos (tuple): The ending position [x, y] of the pawn.

        Returns:
            bool: True if the move is possible, False otherwise.
            str: A string describing why the move is not possible.
        """
        # Check if the start and end positions are within the board bounds
        if not self.is_position_within_board(start_pos):
            return False, "It is not possible to move from outside the board."
        if not self.is_position_within_board(end_pos):
            return False, "It is not possible to move outside the board: " + str(
                end_pos
            )

        # We can't move to the same position
        if start_pos == end_pos:
            return False, "It is not possible to move to the same position."

        start_level = self.board[start_pos[0]][start_pos[1]]
        end_level = self.board[end_pos[0]][end_pos[1]]

        # Check if the end position is not terminated
        if end_level == 4:
            return False, "It is not possible to move on a terminated tower."

        # Check if the end position is not to high
        if end_level - start_level > 1:
            return False, "It is not possible to move two levels in one move."

        # Check if the end position is adjacent to the start position
        if not self.is_position_adjacent(start_pos, end_pos):
            return False, "It is not possible to move that far."

        # Check if the end position is not occupied by another pawn
        if self.is_pawn_on_position(end_pos):
            return False, "It is not possible to move on another pawn."

        return True, "The move is possible."

    def is_position_within_board(self, position: Tuple[int, int]):
        """
        Checks if a position is within the bounds of the game board.

        Args:
            position (tuple): The position [x, y] to check.

        Returns:
            bool: True if the position is within the board bounds, False otherwise.
        """
        x, y = position
        return 0 <= x < self.board_size and 0 <= y < self.board_size

    def is_position_adjacent(
        self, position1: Tuple[int, int], position2: Tuple[int, int]
    ):
        """
        Checks if two positions are adjacent to each other.

        Args:
            position1 (tuple): The first position [x1, y1].
            position2 (tuple): The second position [x2, y2].

        Returns:
            bool: True if the positions are adjacent, False otherwise.
        """
        x1, y1 = position1
        x2, y2 = position2
        return abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1 and (x1 != x2 or y1 != y2)

    def is_pawn_on_position(self, position: Tuple[int, int]):
        """
        Checks if a pawn is on a position.

        Args:
            position (tuple): The position [x, y] to check.

        Returns:
            bool: True if a pawn is on the position, False otherwise.
        """
        for pawn in self.pawns:
            if pawn.pos == position:
                return True
        return False

    def is_build_possible(
        self, builder_position: Tuple[int, int], build_position: Tuple[int, int]
    ):
        """
        Checks if a build from the builder position is possible.

        Args:
            builder_position (tuple): The position [x, y] of the builder pawn.
            build_position (tuple): The position [x, y] of the build.

        Returns:
            bool: True if the build is possible, False otherwise.
            str: A string describing why the build is not possible.
        """
        # Check if the builder position is within the board bounds
        if not self.is_position_within_board(builder_position):
            return False, "It is not possible to build from outside the board."

        # Check if the build position is within the board bounds
        if not self.is_position_within_board(build_position):
            return False, "It is not possible to build outside the board."

        # We can't build on the same position
        if builder_position == build_position:
            return False, "It is not possible to build where you are standing."

        # Check if the build position is not terminated
        if self.board[build_position[0]][build_position[1]] == 4:
            return False, "It is not possible to build on a terminated tower."

        # Check if the build position is adjacent to the builder position
        if not self.is_position_adjacent(builder_position, build_position):
            return False, "It is not possible to build that far."

        # Check if the build position is not occupied by another pawn
        if self.is_pawn_on_position(build_position):
            return False, "It is not possible to build on another pawn."

        return True, "The build is possible."

    def get_playing_pawn(self):
        """
        Gets the pawn of the current player.

        Returns:
            Pawn: The pawn of the current player.
        """
        return self.pawns[self.pawn_turn - 1]

    def get_possible_movement_positions(self, pawn: Pawn):
        """
        Gets all the possible moves for a given pawn.

        Args:
            pawn (Pawn): The pawn for which to get the possible moves.

        Returns:
            list: A list of all the possible moves for the given pawn.
        """
        possible_moves = []

        # If pwan position is None, it means it has not been placed yet
        # Every position is possible except the ones occupied by other pawns
        # and the ones where tower are terminated
        if pawn.pos == (None, None):
            for x in range(self.board_size):
                for y in range(self.board_size):
                    if self.board[x][y] != 4 and not self.is_pawn_on_position((x, y)):
                        possible_moves.append((x, y))
            return possible_moves

        # Get all the possible moves
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x == 0 and y == 0:
                    continue
                move_possible, _ = self.is_move_possible(
                    pawn.pos, (pawn.pos[0] + x, pawn.pos[1] + y)
                )
                if move_possible:
                    possible_moves.append((pawn.pos[0] + x, pawn.pos[1] + y))

        return possible_moves

    def get_possible_building_positions(self, pawn: Pawn):
        """
        Gets all the possible builds for a given pawn, supposing it has already moved.

        Args:
            pawn (Pawn): The pawn for which to get the possible builds.

        Returns:
            list: A list of all the possible builds for the given pawn.
        """
        possible_builds = []

        # Get all the possible builds
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x == 0 and y == 0:
                    continue
                build_possible, _ = self.is_build_possible(
                    pawn.pos, (pawn.pos[0] + x, pawn.pos[1] + y)
                )
                if build_possible:
                    possible_builds.append((pawn.pos[0] + x, pawn.pos[1] + y))

        return possible_builds

    def place_pawn(self, position: Tuple[int, int]) -> Tuple[bool, str]:
        """
        Places a pawn on the board.

        Args:
            position (tuple): The position [x, y] to place the pawn.

        Returns:
            bool: True if the pawn was placed, False otherwise.
            str: A string describing why the pawn was not placed.
        """
        # Check if the game is over
        if self.is_game_over():
            return False, "The game is over."

        # Check if the pawn has already been placed
        if self.get_playing_pawn().pos != (None, None):
            return False, "The pawn has already been placed."

        # Check if the position is valid
        if not self.is_position_within_board(position):
            return False, "The position is not within the board bounds."

        # Check if the position is not occupied by another pawn
        if self.is_pawn_on_position(position):
            return False, "The position is already occupied by another pawn."

        # Get the pawn of the current player
        pawn = self.get_playing_pawn()

        # Place the pawn
        pawn.pos = position

        # Next player's turn
        self.next_turn()

        return True, "The pawn was placed."

    def play_move(
        self, move_vector: Tuple[int, int], build_vector: Tuple[int, int]
    ) -> Tuple[bool, str]:
        """
        Plays a move on the board with the current playing pawn.

        Args:
            move_vector (tuple): The displacement vector [x, y] to apply to the pawn, (-1, 1) for example.
            build_vector (tuple): The build vector [x, y] to apply to the pawn, (-1, 1) for example.

        Returns:
            bool: True if the move was played, False otherwise.
            str: A string describing why the move was not played.
        """
        # Check if the game is over
        if self.is_game_over():
            return False, "The game is over."

        # Get the pawn of the current player
        pawn = self.get_playing_pawn()

        # Check if the pawn has been placed
        if pawn.pos == (None, None):
            return False, "The pawn has not been placed yet."

        # Check if their is any possible move
        possible_moves = self.get_possible_movement_positions(pawn)
        if len(possible_moves) == 0:
            self.next_turn()
            return True, "There is no possible move to play, the pawn is stuck."

        # === MOVE ===
        # Check if the vector is valid
        disp_vector_valid, reason = self.is_vector_valid(move_vector)
        if not disp_vector_valid:
            return False, reason

        # Check if the move is possible
        initial_pos = pawn.pos
        new_pos = (
            pawn.pos[0] + move_vector[0],
            pawn.pos[1] + move_vector[1],
        )
        move_possible, reason = self.is_move_possible(pawn.pos, new_pos)

        if not move_possible:
            return False, reason

        # Apply the move
        pawn.move(new_pos)

        # Check if the tower is terminated
        if self.board[pawn.pos[0]][pawn.pos[1]] == 3:
            self.winner_player_number = pawn.player_number
            return True, "The move was played and the game is over."

        # === BUILD ===
        # Check if the vector is valid
        const_vector_valid, reason = self.is_vector_valid(build_vector)
        if not const_vector_valid:
            # Reverse the move
            pawn.move(initial_pos)
            return False, reason

        # Check if their is any possible build
        # No need to check, it is always possible to build after a move

        # Check if the build is possible
        build_pos = (
            pawn.pos[0] + build_vector[0],
            pawn.pos[1] + build_vector[1],
        )

        build_possible, reason = self.is_build_possible(pawn.pos, build_pos)

        if not build_possible:
            # The move was played but the build is not possible
            # Reverse the move
            pawn.move(initial_pos)
            return False, reason

        # Build the tower
        self.board[build_pos[0]][build_pos[1]] += 1

        if self.is_everyone_stuck():
            self.winner_player_number = pawn.player_number
            return True, "No one can play, the game is over."

        # Change the turn
        self.next_turn()

        return True, "The move was played."

    def is_vector_valid(self, vector: Tuple[int, int]):
        """
        Checks if a vector is valid.

        Args:
            vector (tuple): The vector to check.

        Returns:
            bool: True if the vector is valid, False otherwise.
            str: A string describing why the vector is not valid.
        """

        # Check if the vector is a tuple
        if not isinstance(vector, tuple):
            return False, "The vector is not a tuple, but a {}.".format(type(vector))

        # Check if the vector is a 2D vector
        if len(vector) != 2:
            return False, "The vector is not a 2D vector, but a {}D vector.".format(
                len(vector)
            )

        # Check if the vector is a valid displacement vector
        if not vector[0] in [-1, 0, 1] or not vector[1] in [-1, 0, 1]:
            return (
                False,
                "The vector is not a valid displacement vector (" + str(vector) + ").",
            )

        # The vector can't be a null vector
        if vector == (0, 0):
            return False, "The vector needs to go somewhere (0, 0)."

        return True, "The vector is valid."

    def is_game_over(self):
        """
        Checks if the game is over.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        if self.winner_player_number is not None:
            return True

        if self.is_everyone_stuck():
            return True

    def is_everyone_stuck(self):
        """
        Checks if everyone is stuck.

        Returns:
            bool: True if everyone is stuck, False otherwise.
        """
        for pawn in self.pawns:
            if len(self.get_possible_movement_positions(pawn)) > 0:
                return False

        return True

    def next_turn(self):
        """
        Changes the turn.
        """
        self.pawn_turn += 1
        if self.pawn_turn > self.nb_pawns:
            self.pawn_turn = 1

        self.turn_number += 1

    def copy(self) -> "Board":
        """
        Creates a copy of the board.

        Returns:
            Board: A copy of the board.
        """
        # Create a new board
        board_copy = Board(self.board_size)

        # Copy the board
        for x in range(self.board_size):
            for y in range(self.board_size):
                board_copy.board[x][y] = self.board[x][y]

        # Copy the pawns
        board_copy.pawns = [pawn.copy() for pawn in self.pawns]

        # Copy the other attributes
        board_copy.pawn_turn = self.pawn_turn
        board_copy.turn = self.turn_number
        board_copy.winner_player_number = self.winner_player_number

        return board_copy

    def __repr__(self) -> str:
        """
        Returns a string representation of the board.

        Returns:
            str: A string representation of the board.
        """
        output = "\n"

        for y in range(self.board_size - 1, -1, -1):
            for x in range(self.board_size):
                # Check if their is a pawn at this position
                pawn = None
                for p in self.pawns:
                    if p.pos == (x, y):
                        pawn = p
                        break
                pawn_number = str(pawn.number) if pawn is not None else "_"
                output += pawn_number + str(self.board[x][y]) + " "
            output += "\n"

        return output
