# ===============================================================================
# Imports
# ===============================================================================
import math

import abstract
from players.better_h_player import CENTER_BOARD, MAX_DISTANCE_FROM_CENTER
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP, BOARD_ROWS, MY_COLORS, \
    BOARD_COLS, BACK_ROW
import time
from players import simple_player
from collections import defaultdict

# ===============================================================================
# Globals
# ===============================================================================

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5


# ===============================================================================
# Player
# ===============================================================================

class Player(simple_player.Player):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        simple_player.Player.__init__(self, setup_time, player_color, time_per_k_turns, k)
        # Initialize Minimax algorithm, still not running anything
        self.minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time,
                                                   self.selective_deepening_criterion)

    def selective_deepening_criterion(self, state):
        # capture is a more dangerous/significant move than a regular movement and therefore it worths deeping.
        capture_moves = state.calc_capture_moves()
        if capture_moves is not None:
            return True
        return False

    def get_move(self, game_state, possible_moves):
        self.clock = time.process_time()
        # we want to give more time to turns in which the amount of possible moves is bigger.
        if len(possible_moves) < 5 and self.turns_remaining_in_round > 0:
            # in case the amount of possible moves is less than 6 we reduce the time for the current move
            self.time_for_current_move = 0.7 * (self.time_remaining_in_round / self.turns_remaining_in_round - 0.05)
            # print('{} possible moves'.format(len(possible_moves)))
        else:
            # otherwise, we divided the time uniformly.
            self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        # if there is only one possible move we still have to update the counters!
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

        # initializing a counter of the amount of times the same move was returned from minimax in a row.
        same_rounds_counter = 0

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

            if prev_alpha == alpha and move.origin_loc == best_move.origin_loc and \
                    move.target_loc == best_move.target_loc and current_depth > 2:
                # if the move and the alpha which were returned are the same as the former ones, we increase the counter
                # as well, we increase the counter only if the current depth is more than 5 because we don't want to
                # judge according to the first iterations which may not be testifying.
                same_rounds_counter += 1
            else:
                same_rounds_counter = 0

            if self.turns_remaining_in_round > 1:
                """
                We want to save time for future turns.
                We will save time for future turns only if there are at least 2 turns in the round ahead.
                """
                if same_rounds_counter == 3:
                    # print('{} times in a row the same move'.format(same_rounds_counter))
                    best_move = move
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

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'improved_better_h')

    def is_cell_in_board(self, cell):
        return (cell[0] >= 0 and cell[0] < BOARD_ROWS and cell[1] >= 0 and
                cell[1] < BOARD_COLS)

    def distance_from_center(self, cell):

        d_rows = abs(cell[0] - CENTER_BOARD)
        d_cols = abs(cell[1] - CENTER_BOARD)
        return math.sqrt(pow(d_rows, 2) + pow(d_cols, 2))

    def grade_distance(self, distance):
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
        my_loc_grade = 0
        op_loc_grade = 0
        # now we want to assess how good for us is the state of the board.
        curr_color = None
        op_curr_color = None
        is_opp = False
        for loc, loc_val in state.board.items():
            if loc_val != EM:
                piece_counts[loc_val] += 1
                if loc_val in MY_COLORS[self.color]:
                    my_rows_score += loc[0]
                    curr_color = self.color
                    op_curr_color = opponent_color
                    is_opp = False

                    if loc_val == KING_COLOR[self.color]:
                        my_kings_dist_score += self.grade_distance(
                            self.distance_from_center(loc))
                else:
                    op_rows_score += (BOARD_ROWS - loc[0] - 1)
                    curr_color = opponent_color
                    op_curr_color = self.color
                    is_opp = True
                    if loc_val == KING_COLOR[opponent_color]:
                        op_kings_dist_score += self.grade_distance(
                            self.distance_from_center(loc))

                # in order to assess how good is the board state for us, we should encourage positions which are good for us.
                # we will encourage, at the earlier stages of the game, being in the edges of the board because it is
                # either making a pawn to be a king or protecting a location from the opponent.
                # we will encourage kings. kings are good for us.

                loc_grade = 0
                if loc_val == KING_COLOR[curr_color]:
                    # first of all we like kings. they are good for us. Thus, we give kings high score.
                    loc_grade = 5
                elif piece_counts[PAWN_COLOR[op_curr_color]] + piece_counts[PAWN_COLOR[op_curr_color]] <= 5:
                    # it means that less than 5 pawns are left and we are in an advance stage of the game.
                    # we should encourage our pawns to become kings.
                    loc_grade = (8 - loc[0] - BACK_ROW[curr_color]) / 2 + 2
                elif loc[0] == BACK_ROW[curr_color]:
                    # the pawn is becoming a king
                    loc_grade = 5
                elif loc[0] == BOARD_ROWS - BACK_ROW[curr_color]:
                    # a pawn is being protecting
                    loc_grade = 4.25
                elif loc[1] == 0 or loc[1] == 7:
                    # in this case the opponent cannot jump over those pawns
                    loc_grade = 3.5
                else:
                    # there is nothing special
                    loc_grade = 2.5
                if is_opp:
                    op_loc_grade += loc_grade
                else:
                    my_loc_grade += loc_grade

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
            return my_u + my_rows_score + my_kings_dist_score + my_loc_grade - \
                   (op_u + op_rows_score + op_kings_dist_score + op_loc_grade)

# c:\python35\python.exe run_game.py 3 3 3 y simple_player random_player
