from santorinai.player import Player
from random import choice


class RandomPlayer(Player):
    """
    A player that places his pawns and moves them randomly
    """
    def __init__(self, player_number, log_level=0) -> None:
        super().__init__(player_number, log_level)

    def name(self):
        return "Randy Random"

    def place_pawn(self, board, pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        my_choice = choice(available_positions)
        return my_choice

    def play_move(self, board):
        # Choose pawn randomly
        l_pawns = board.get_player_pawns(self.player_number)
        pawn = choice(l_pawns)

        # Get movement positions
        available_positions = board.get_possible_movement_positions(pawn)
        if len(available_positions) == 0:
            # The pawn cannot move
            return pawn.number, None, None

        my_move_choice = choice(available_positions)

        # Simulate the move (Need to use pawn copy since returned pawn will be moved)
        pawn.move(my_move_choice)

        # Get construction positions for the new position
        available_positions = board.get_possible_building_positions(pawn)
        my_build_choice = choice(available_positions)

        return pawn.number, my_move_choice, my_build_choice
