from abc import ABC, abstractmethod, abstractproperty
from typing import Tuple

from santorinai.board import Board
from santorinai.pawn import Pawn
from typing import Tuple


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
    def place_pawn(self, board: Board, pawn: Pawn) -> Tuple[int, int]:
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
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Play a move given a board
        :param board: the board
        :param pawn: the pawn that needs to be moved and that needs to build
        :return: two positions of the form (x1, y1), (x2, y2)

        The first coordinate corresponds to the new position of the pawn
        The second coordinate corresponds to the position of the construction of the tower

        Return example: (2, 2), (2, 3) means that the player wants to move the pawn at
        at center of the board and build a tower at the top of his position
        """
        pass
