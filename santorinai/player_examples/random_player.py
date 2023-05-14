from santorinai.player import Player

from random import choice


class RandomPlayer(Player):
    """
    A player that places his pawns and moves them randomly
    """

    def name(self):
        return "Randy Random"

    def place_pawn(self, board, pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        my_choice = choice(available_positions)
        return my_choice

    def play_move(self, board, pawn):
        my_initial_position = pawn.pos

        # Get movement positions
        available_positions = board.get_possible_movement_positions(pawn)
        my_move_choice = choice(available_positions)

        # Simulate the move
        pawn.move(my_move_choice)

        # Get construction positions for the new position
        available_positions = board.get_possible_building_positions(pawn)
        my_build_choice = choice(available_positions)

        return my_move_choice, my_build_choice
