import sys
sys.path.append('..')

from santorinai.tester import Tester
from santorinai.player_examples.random_player import RandomPlayer
from santorinai.player_examples.first_choice_player import FirstChoicePlayer

# Init the tester
tester = Tester()
tester.verbose_level = 2  # 0: no output, 1: Each game results, 2: Each move summary
tester.delay_between_moves = 0.5  # Delay between each move in seconds
tester.display_board = True  # Display a graphical view of the board in a window

# Init the players
my_player = FirstChoicePlayer()
random_payer = RandomPlayer()

# Play 100 games
tester.play_1v1(my_player, random_payer, nb_games=100)
