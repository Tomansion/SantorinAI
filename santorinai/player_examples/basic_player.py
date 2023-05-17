from santorinai.player import Player
from santorinai.board import Board
from random import choice


class BasicPlayer(Player):
    """
    A player that answer to simple rules:
    - Place first pawn on the first randomly
    - Place second pawn next to the first one if possible
    - If there is a winning move, play it.
    - If we can prevent the opponent from winning, do it.
    - Move up if we can
    - Build randomly

    :log_level: 0: no output, 1: Move choices
    """

    def __init__(self, log_level=0) -> None:
        super().__init__()
        self.log_level = log_level

    def name(self):
        return "Extra BaThick!"

    def get_ally_pawn(self, board, our_pawn):
        for pawn in board.pawns:
            if (
                pawn.number != our_pawn.number
                and pawn.player_number == our_pawn.player_number
            ):
                return pawn

    def get_enemy_pawns(self, board, our_pawn):
        pawns = []
        for pawn in board.pawns:
            if pawn.player_number != our_pawn.player_number:
                pawns.append(pawn)
        return pawns

    def get_winning_moves(self, board: Board, pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        winning_moves = []
        for pos in available_positions:
            if board.board[pos[0]][pos[1]] == 3:
                winning_moves.append(pos)

        return winning_moves

    def place_pawn(self, board: Board, pawn):
        ally_pawn = self.get_ally_pawn(board, pawn)
        available_positions = board.get_possible_movement_positions(pawn)

        if ally_pawn.pos == (None, None):
            # First pawn to place
            return choice(available_positions)

        for pos in available_positions:
            if board.is_position_adjacent(pos, ally_pawn.pos):
                return pos

        return choice(available_positions)

    def play_move(self, board, pawn):
        available_positions = board.get_possible_movement_positions(pawn)

        current_level = board.board[pawn.pos[0]][pawn.pos[1]]
        best_spot = None
        best_spot_level = 0
        for pos in available_positions:
            if board.board[pos[0]][pos[1]] == 3:
                # We can win!
                if self.log_level:
                    print("Winning move")
                return pos, (None, None)

            pos_level = board.board[pos[0]][pos[1]]
            if pos_level <= current_level + 1 and pos_level > best_spot_level:
                # We can go up
                best_spot = pos
                best_spot_level = pos_level

        # Check if we can prevent the opponent from winning
        enemy_pawns = self.get_enemy_pawns(board, pawn)
        for enemy_pawn in enemy_pawns:
            winning_moves = self.get_winning_moves(board, enemy_pawn)
            for winning_move in winning_moves:
                for available_pos in available_positions:
                    if board.is_position_adjacent(winning_move, available_pos):
                        # We can prevent the opponent from winning
                        # Building on the winning move
                        if self.log_level:
                            print("Preventing opponent from winning")
                        return available_pos, winning_move

        # Move up if we can
        if best_spot:
            if self.log_level:
                print("Moving up")
            pawn.move(best_spot)
            build_positions = board.get_possible_building_positions(pawn)
            return best_spot, choice(build_positions)

        if self.log_level:
            print("Random move")

        # play randomly
        return choice(board.get_possible_movement_and_building_positions(pawn))
