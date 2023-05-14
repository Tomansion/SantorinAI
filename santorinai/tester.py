from santorinai.player import Player
from santorinai.board import Board
from santorinai.board_displayer.board_displayer import init_window, update_board
from time import sleep


class Tester:
    """
    Run the games with SantorinAI playes, do statistics display the results
    """

    verbose_level = 2
    delay_between_moves = 0
    display_board = True

    def display_message(self, message, verbose_level=1):
        """
        Display a message if verbose is True

        Args:
            message (str): the message to display
        """
        if self.verbose_level >= verbose_level:
            print(message)

    def play_1v1(self, player1: Player, player2: Player, nb_games: int = 1):
        """
        Play a 1v1 game between player1 and player2

        Args:
            player1 (Player): the first player
            player2 (Player): the second player
        """
        NB_PLAYERS = 2
        NB_PAWNS = NB_PLAYERS * 2

        nb_victories = [0, 0]

        # Check if the players are objects of the Player class
        if not isinstance(player1, Player):
            raise TypeError("player1 should be an object of the Player class")
        if not isinstance(player2, Player):
            raise TypeError("player2 should be an object of the Player class")

        players = [player1, player2]

        # Initialize the window
        if self.display_board:
            window = init_window([player1.name(), player2.name()])

        # Play the games
        for game_nb in range(1, nb_games + 1):
            self.display_message(f"Game {game_nb}", 1)

            # Initialize the board
            board = Board(NB_PLAYERS)

            # Placement the pawns
            for pawn_nb in range(1, NB_PAWNS + 1):
                board_copy = board.copy()
                current_pawn = board_copy.get_playing_pawn()

                # Ask the player where to place the pawn
                player = players[pawn_nb % NB_PLAYERS]
                self.display_message(
                    f"Player {player.name()} is placing pawn {pawn_nb}", 2
                )
                position_choice = player.place_pawn(board_copy, current_pawn)

                # Place the pawn
                success, reason = board.place_pawn(position_choice)

                if not success:
                    self.display_message(
                        f"   Pawn placed at an invalid position: {reason}", 1
                    )
                    self.display_message(f"   Player {player.name()} loses")
                    nb_victories[(pawn_nb + 1) % NB_PLAYERS] += 1
                    break

                self.display_message(f"   Pawn placed at position {position_choice}", 2)
                if self.display_board:
                    update_board(window, board)
                sleep(self.delay_between_moves)

            # Play the game
            self.display_message(f"\nPlaying the game")
            while not board.is_game_over():
                current_pawn = board.get_playing_pawn()
                self.display_message(f"   Current pawn: {current_pawn}", 2)

                # Check if the player can move
                if len(board.get_possible_movement_positions(current_pawn)) == 0:
                    self.display_message(f"   The pawn cannot move", 2)
                    # We don't ask the player to move, we just skip his turn
                    continue

                board_copy = board.copy()
                current_pawn_copy = board_copy.get_playing_pawn()

                # Ask the player where to move the pawn
                player = players[current_pawn.player_number - 1]
                self.display_message(
                    f"Player {player.name()} is moving pawn {current_pawn.number}", 2
                )
                move_choice, build_choice = player.play_move(
                    board_copy, current_pawn_copy
                )

                # Move the pawn
                success, reason = board.play_move(move_choice, build_choice)

                if not success:
                    self.display_message(
                        f"   Pawn moved at an invalid position: {reason}", 1
                    )
                    self.display_message(f"   Player {player.name()} loses")
                    nb_victories[(current_pawn.player_number) % NB_PLAYERS] += 1
                    break

                self.display_message(
                    f"   Pawn moved at position {move_choice} and built at position {build_choice}",
                    2,
                )
                self.display_message(board, 2)
                if self.display_board:
                    update_board(window, board)
                sleep(self.delay_between_moves)

            # Game is over
            winer_number = board.winner_player_number
            if winer_number is None:
                self.display_message("Draw")
            else:
                self.display_message(f"Player {players[winer_number - 1].name()} wins!")
                nb_victories[winer_number - 1] += 1

        # Display the results
        print(f"\nResults:")
        print(f"Player {players[0].name()} won {nb_victories[0]} times")
        print(f"Player {players[1].name()} won {nb_victories[1]} times")
