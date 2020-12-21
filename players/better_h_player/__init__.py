# ===============================================================================
# Imports
# ===============================================================================

from players import simple_player
import abstract
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
from checkers.consts import BOARD_COLS, BOARD_ROWS, EM, MY_COLORS, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP
import time
from collections import defaultdict
import math
# ===============================================================================
# Globals
# ===============================================================================

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5
CENTER_BOARD = 3.5  # the middle of 0 and 7
MAX_DISTANCE_FROM_CENTER = 4.95  # the distance from (0, 0) to (3.5, 3.5)

# ===============================================================================
# Player
# ===============================================================================


class Player(simple_player.Player):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        simple_player.Player.__init__(self, setup_time, player_color, time_per_k_turns, k)
        # Initialize Minimax algorithm, still not running anything
        self.minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time,
                                                   self.selective_deepening_criterion)

    def get_move(self, game_state, possible_moves):
        self.clock = time.process_time()
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        if len(possible_moves) == 1:
            if self.turns_remaining_in_round == 1:
                # In case this was the last turn, we need to reset the counters
                self.time_remaining_in_round = self.time_per_k_turns
                self.turns_remaining_in_round = self.k
            else:
                # in case there are more turns in this round, we update the counters properly.
                self.turns_remaining_in_round -= 1
                self.time_remaining_in_round -= (time.process_time() - self.clock)
            # anyway we return the only possible move.
            return possible_moves[0]

        current_depth = 1
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything


        # Iterative deepening until the time runs out.
        while True:

            print('going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}'.format(
                current_depth,
                self.time_for_current_move - (time.process_time() - self.clock),
                prev_alpha,
                best_move))

            try:
                (alpha, move), run_time = run_with_limited_time(
                    self.minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {},
                    self.time_for_current_move - (time.process_time() - self.clock))
            except (ExceededTimeError, MemoryError):
                print('no more time, achieved depth {}'.format(current_depth))
                break

            if self.no_more_time():
                print('no more time')
                break

            prev_alpha = alpha
            best_move = move

            if alpha == INFINITY:
                print('the move: {} will guarantee victory.'.format(best_move))
                break

            if alpha == -INFINITY:
                print('all is lost')
                break

            current_depth += 1

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.process_time() - self.clock)
        return best_move

    # def score(self, piece_counts, color):
    #     score = ((PAWN_WEIGHT * piece_counts[PAWN_COLOR[color]]) +
    #              (KING_WEIGHT * piece_counts[KING_COLOR[color]]))
    #     return score

    def is_cell_in_board(cell):
        return (cell[0] >= 0 and cell[0] < BOARD_ROWS and cell[1] >= 0 and
                cell[1] < BOARD_COLS)

    def distance_from_center(cell):

        d_rows = abs(cell[0]-CENTER_BOARD)
        d_cols = abs(cell[1]-CENTER_BOARD)
        return math.sqrt(pow(d_rows, 2) + pow(d_cols, 2))

    def grade_distance(distance):
        return MAX_DISTANCE_FROM_CENTER - distance

    def utility(self, state):
        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY
        if state.turns_since_last_jump >= MAX_TURNS_NO_JUMP:
            return 0

        piece_counts = defaultdict(lambda: 0)

        my_rows_score = 0
        op_rows_score = 0
        my_kings_dist_score = 0
        op_kings_dist_score = 0
        opponent_color = OPPONENT_COLOR[self.color]
        for loc, loc_val in state.board.items():
            if loc_val != EM:
                piece_counts[loc_val] += 1
                if loc_val in MY_COLORS[self.color]:
                    my_rows_score += loc[0]

                    if loc_val == KING_COLOR[self.color]:
                        my_kings_dist_score += self.grade_distance(
                            self.distance_from_center(loc))
                else:
                    op_rows_score += (BOARD_ROWS-loc[0])
                    if loc_val == KING_COLOR[opponent_color]:
                        op_kings_dist_score += self.grade_distance(
                            self.distance_from_center(loc))

        my_u = ((PAWN_WEIGHT * piece_counts[PAWN_COLOR[self.color]]) +
                (KING_WEIGHT * piece_counts[KING_COLOR[self.color]]))
        op_u = ((PAWN_WEIGHT * piece_counts[PAWN_COLOR[opponent_color]]) +
                (KING_WEIGHT * piece_counts[KING_COLOR[opponent_color]]))
        if my_u == 0:
            # I have no tools left
            return -INFINITY
        elif op_u == 0:
            # The opponent has no tools left
            return INFINITY
        else:
            return my_u + my_rows_score + my_kings_dist_score - (op_u + op_rows_score + op_kings_dist_score)

    def selective_deepening_criterion(self, state):
        # Simple player does not selectively deepen into certain nodes.
        return False