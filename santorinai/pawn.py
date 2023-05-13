class pawn:
    def __init__(self, pawn_number, player_number):
        """
        Initialize a pawn
        :param pawn_number: the number of the pawn
        :param player_number: the player number of the pawn
        """
        self.pos = (None, None)
        self.pawn_number = pawn_number
        self.player_number = player_number

    def __repr__(self):
        return f"pawn {self.pawn_number} of player {self.player_number} at position {self.pos}"
