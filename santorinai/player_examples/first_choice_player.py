from santorinai.player import Player


class FirstChoicePlayer(Player):
    """
    A player that places his pawns and moves them at the first possible position
    """

    def name(self):
        return "Firsty First"

    def place_pawn(self, board, pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        my_choice = available_positions[0]
        return my_choice

    def play_move(self, board, pawn):
        my_initial_position = pawn.pos

        # Get movement positions
        available_positions = board.get_possible_movement_positions(pawn)
        my_move_choice = available_positions[0]

        # Simulate the move
        pawn.move(my_move_choice)

        # Get construction positions
        available_positions = board.get_possible_building_positions(pawn)
        my_build_choice = available_positions[0]

        my_move_vector = (
            my_move_choice[0] - my_initial_position[0],
            my_move_choice[1] - my_initial_position[1],
        )

        my_build_vector = (
            my_build_choice[0] - my_move_choice[0],
            my_build_choice[1] - my_move_choice[1],
        )

        return my_move_vector, my_build_vector
