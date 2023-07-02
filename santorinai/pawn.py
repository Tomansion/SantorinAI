from typing import Tuple


class Pawn:
    def __init__(self, number: int, player_number: int):
        """
        Initialize a pawn
        :param number: the number of the pawn
        :param player_number: the player number of the pawn
        """
        self.pos = (None, None)
        self.number = number
        self.player_number = player_number

    def move(self, new_pos: Tuple[int, int]):
        """
        Move the pawn to the new position
        :param new_pos: the new position of the pawn
        """
        self.pos = new_pos

    def copy(self) -> "Pawn":
        """
        Return a copy of the pawn
        :return: a copy of the pawn
        """
        new_pawn = Pawn(self.number, self.player_number)
        new_pawn.pos = self.pos
        return new_pawn

    def __repr__(self):
        return (
            f"pawn {self.number} of player {self.player_number} at position {self.pos}"
        )
