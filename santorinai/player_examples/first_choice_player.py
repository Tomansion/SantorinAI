from santorinai.player import Player
from santorinai.board import Board
from santorinai.pawn import Pawn


class FirstChoicePlayer(Player):
    """
    A player that places his pawns and moves them at the first possible position
    """

    def name(self):
        return "Firsty First"

    def place_pawn(self, board: Board, pawn: Pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        my_choice = available_positions[0]
        return my_choice

    def play_move(self, board: Board, pawn: Pawn):
        # Get movement positions
        available_move_positions = board.get_possible_movement_positions(pawn)
        if len(available_move_positions) == 0:
            # The pawn cannot move
            return None, None

        my_move_choice = available_move_positions[0]

        # Simulate the move (this will not impact the actual board)
        pawn.move(my_move_choice)

        # Get construction positions
        available_build_positions = board.get_possible_building_positions(pawn)
        if len(available_build_positions) == 0:
            # The pawn cannot build
            raise Exception("Pawn cannot build")

        # Their is always at least one position available
        my_build_choice = available_build_positions[0]

        return my_move_choice, my_build_choice
