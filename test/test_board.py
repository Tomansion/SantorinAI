# Test file for board.py

import unittest

from santorinai.board import Board


class TestBoardTwoPlayers(unittest.TestCase):
    NB_PLAYERS = 2

    def setUp(self):
        self.board = Board(self.NB_PLAYERS)

    def test_init(self):
        # Test if the board is initialized correctly
        self.assertEqual(self.board.board_size, 5)
        self.assertEqual(
            self.board.board,
            [
                [0 for _ in range(self.board.board_size)]
                for _ in range(self.board.board_size)
            ],
        )
        self.assertEqual(self.board.pawn_turn, 1)
        self.assertEqual(self.board.winner_player_number, None)

        # Test if the pawns are initialized correctly
        self.assertEqual(len(self.board.pawns), self.NB_PLAYERS * 2)

        # Pawn n°1 belongs to player n°1
        # Pawn n°2 belongs to player n°2
        # Pawn n°3 belongs to player n°1
        # Pawn n°4 belongs to player n°2

        self.assertEqual(self.board.pawns[0].pawn_number, 1)
        self.assertEqual(self.board.pawns[0].player_number, 1)
        self.assertEqual(self.board.pawns[1].pawn_number, 2)
        self.assertEqual(self.board.pawns[1].player_number, 2)
        self.assertEqual(self.board.pawns[2].pawn_number, 3)
        self.assertEqual(self.board.pawns[2].player_number, 1)
        self.assertEqual(self.board.pawns[3].pawn_number, 4)
        self.assertEqual(self.board.pawns[3].player_number, 2)

    def test_is_move_possible(self):
        # Test if it is not possible to move from outside the board
        self.assertFalse(self.board.is_move_possible((-1, -1), (0, 0))[0])
        self.assertFalse(self.board.is_move_possible((0, 0), (-1, -1))[0])

        # Test if it is not possible to move to the same position
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 0))[0])

        # Test if it is not possible to move on a terminated tower
        self.board.board[0][0] = 0
        self.board.board[0][1] = 4
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])

        # Test if it is not possible to move two levels in one move
        self.board.board[0][0] = 0
        self.board.board[0][1] = 2
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])
        self.board.board[0][0] = 1
        self.board.board[0][1] = 3
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])
        self.board.board[0][1] = 0

        # Test if it is not possible to move too far
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 2))[0])
        self.assertFalse(self.board.is_move_possible((0, 0), (2, 0))[0])

        # Test if it is not possible to move on another pawn
        self.board.pawns[0].pos = (0, 1)
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])

        # Test if it is possible to move on an empty neighboring position
        self.assertTrue(self.board.is_move_possible((2, 2), (2, 3))[0])
        self.assertTrue(self.board.is_move_possible((2, 2), (1, 2))[0])
        self.assertTrue(self.board.is_move_possible((2, 2), (1, 1))[0])
        self.assertTrue(self.board.is_move_possible((2, 2), (3, 3))[0])

    def test_is_position_within_board(self):
        # Test if it is not possible to move from outside the board
        self.assertFalse(self.board.is_position_within_board((-1, -1)))
        self.assertFalse(self.board.is_position_within_board((0, -1)))
        self.assertFalse(self.board.is_position_within_board((-1, 0)))

        # Test if it is possible to move within the board
        self.assertTrue(self.board.is_position_within_board((0, 0)))
        self.assertTrue(self.board.is_position_within_board((0, 1)))
        self.assertTrue(self.board.is_position_within_board((1, 0)))
        self.assertTrue(self.board.is_position_within_board((1, 1)))

    def test_is_build_possible(self):
        # Test if it is not possible to build from outside the board
        self.assertFalse(self.board.is_build_possible((-1, -1), (0, 0))[0])
        self.assertFalse(self.board.is_build_possible((0, 0), (-1, -1))[0])

        # Test if it is not possible to build on the same position
        self.assertFalse(self.board.is_build_possible((0, 0), (0, 0))[0])

        # Test if it is not possible to build on a terminated tower
        self.board.board[0][0] = 0
        self.board.board[0][1] = 4
        self.assertFalse(self.board.is_build_possible((0, 0), (0, 1))[0])
        self.board.board[0][1] = 0

        # Test if it is not possible to build too far
        self.assertFalse(self.board.is_build_possible((0, 0), (0, 2))[0])
        self.assertFalse(self.board.is_build_possible((0, 0), (2, 0))[0])

        # Test if it is not possible to build on another pawn
        self.board.pawns[0].pos = (0, 1)
        self.assertEqual(
            self.board.is_build_possible((0, 0), (0, 1)),
            (False, "It is not possible to build on another pawn."),
        )

        # Test if it is possible to build on an empty neighboring position
        self.assertTrue(self.board.is_build_possible((2, 2), (2, 3))[0])
        self.assertTrue(self.board.is_build_possible((2, 2), (1, 2))[0])
        self.assertTrue(self.board.is_build_possible((2, 2), (1, 1))[0])
        self.assertTrue(self.board.is_build_possible((2, 2), (3, 3))[0])


class TestBoardThreePlayers(unittest.TestCase):
    NB_PLAYERS = 3

    def setUp(self):
        self.board = Board(self.NB_PLAYERS)

    def test_init(self):
        # Test if the board is initialized correctly
        self.assertEqual(self.board.board_size, 5)
        self.assertEqual(
            self.board.board,
            [
                [0 for _ in range(self.board.board_size)]
                for _ in range(self.board.board_size)
            ],
        )
        self.assertEqual(self.board.pawn_turn, 1)
        self.assertEqual(self.board.winner_player_number, None)

        # Test if the pawns are initialized correctly
        self.assertEqual(len(self.board.pawns), self.NB_PLAYERS * 2)

        # Pawn n°1 belongs to player n°1
        # Pawn n°2 belongs to player n°2
        # Pawn n°3 belongs to player n°3
        # Pawn n°4 belongs to player n°1
        # Pawn n°5 belongs to player n°2
        # Pawn n°6 belongs to player n°3

        self.assertEqual(self.board.pawns[0].pawn_number, 1)
        self.assertEqual(self.board.pawns[0].player_number, 1)
        self.assertEqual(self.board.pawns[1].pawn_number, 2)
        self.assertEqual(self.board.pawns[1].player_number, 2)
        self.assertEqual(self.board.pawns[2].pawn_number, 3)
        self.assertEqual(self.board.pawns[2].player_number, 3)
        self.assertEqual(self.board.pawns[3].pawn_number, 4)
        self.assertEqual(self.board.pawns[3].player_number, 1)
        self.assertEqual(self.board.pawns[4].pawn_number, 5)
        self.assertEqual(self.board.pawns[4].player_number, 2)
        self.assertEqual(self.board.pawns[5].pawn_number, 6)
        self.assertEqual(self.board.pawns[5].player_number, 3)
