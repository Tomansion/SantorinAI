from .pound import Pound


class Board:
    """
    Represents the game board for the Santorini game.

    Attributes:
        pounds (list): A list of Pound objects representing the pawns on the board.
        board_size (int): The size of the square game board.
        board (list): A 2D list representing the current state of the board.
        pound_turn (int): The index of the current player's turn.
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

    def __init__(self, number_of_players):
        """
        Initializes a new instance of the Board class.

        Args:
            number_of_players (int): The number of players in the game.
        """
        self.pounds = []
        for i in range(number_of_players):
            self.pounds.append(
                Pound(player_number=i + 1, pound_number=len(self.pounds) + 1)
            )

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

        self.pound_turn = 0
        self.winner_player_number = None

    def is_move_possible(self, start_pos, end_pos):
        """
        Checks if a move from the start position to the end position is possible.

        Args:
            start_pos (list): The starting position [x, y] of the pawn.
            end_pos (list): The ending position [x, y] of the pawn.

        Returns:
            bool: True if the move is possible, False otherwise.
            str: A string describing why the move is not possible.
        """
        # Check if the start and end positions are within the board bounds
        if not self.is_position_within_board(start_pos):
            return False, "It is not possible to move from outside the board."
        if not self.is_position_within_board(end_pos):
            return False, "It is not possible to move outside the board."

        # We can't move to the same position
        if start_pos == end_pos:
            return False, "It is not possible to move to the same position."

        start_level = self.board[start_pos[0]][start_pos[1]]
        end_level = self.board[end_pos[0]][end_pos[1]]

        # Check if the end position is not terminated
        if end_level == 4:
            return False, "It is not possible to move on a terminated tower."

        # Check if the end position is not to high
        if end_level + 1 > start_level:
            return False, "It is not possible to move two levels in one move."

        # Check if the end position is adjacent to the start position
        if not self.is_position_adjacent(start_pos, end_pos):
            return False, "It is not possible to move that far."

        # Check if the end position is not occupied by another pawn
        for pound in self.pounds:
            if pound.pos == end_pos:
                return False, "It is not possible to move on another pawn."

        return True

    def is_position_within_board(self, position):
        """
        Checks if a position is within the bounds of the game board.

        Args:
            position (list): The position [x, y] to check.

        Returns:
            bool: True if the position is within the board bounds, False otherwise.
        """
        x, y = position
        return 0 <= x < self.board_size and 0 <= y < self.board_size

    def is_position_adjacent(self, position1, position2):
        """
        Checks if two positions are adjacent to each other.

        Args:
            position1 (list): The first position [x1, y1].
            position2 (list): The second position [x2, y2].

        Returns:
            bool: True if the positions are adjacent, False otherwise.
        """
        x1, y1 = position1
        x2, y2 = position2
        return abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1 and (x1 != x2 or y1 != y2)
