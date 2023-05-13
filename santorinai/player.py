from abc import ABC, abstractmethod, abstractproperty

from santorinai.board import Board
from santorinai.pawn import Pawn


class Player:
    """
    A player of Santorini, has a name and can play a move given a board
    """

    @abstractproperty
    def name(self):
        """
        The name of the player
        """
        pass

    @abstractmethod
    def place_pawn(self, board: Board, pawn: Pawn) -> tuple[int, int]:
        """
        Place a pawn given a board
        :param board: the board
        :param pawn: the pawn that needs to be placed
        :return: a position of the form (x, y)

        Return example: (2, 2) means that the player wants to place his pawn at the center of the board
        """
        pass

    @abstractmethod
    def play_move(
        self, board: Board, pawn: Pawn
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Play a move given a board
        :param board: the board
        :param pawn: the pawn that needs to be moved and that needs to build
        :return: two vectors of the form (x1, y1), (x2, y2)

        The first vector is the move of the pawn and the second vector is the
        construction of a building relative to the new position of the pawn

        Return example: (1, 0), (-1, 1) means that the player wants to move the pawn right one tile
         and construct a building at the top left of his new position
        """
        pass
