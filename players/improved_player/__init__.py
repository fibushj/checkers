# ===============================================================================
# Imports
# ===============================================================================

import abstract
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP
import time
from collections import defaultdict
from players import simple_player

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
        """
        this method is the constructor of our player. It is the same as the constructor of simple_player
        except for adding an attribute which will help us to manage the time in a smarter way.
        """
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)
        self.clock = time.process_time()

        # TODO fix comments

        # We are simply providing (remaining time / remaining turns) for each turn in round.
        # Taking a spare time of 0.05 seconds.

        self.turns_remaining_in_round = self.k
        self.time_remaining_in_round = self.time_per_k_turns

        """
        We erased the original line which appeared in the simple_player constructor.
        """
        # self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

        # The idea of our time management is as follows: The first turn will receive half of time_per_k_turns.
        # the second turn will receive quarter of time_per_k_turns, the third one will receive 1/8 and so on.
        # The intuition behind this is that in the beginning we need to predict as much scenarios as possible.

        self.partial_amount = 2
        self.time_for_current_move = self.time_remaining_in_round / self.partial_amount

    def get_move(self, game_state, possible_moves):
        """
        We updated the get_move method in order for it to fit to our time management technique.
        As well, we added a slight change in order to prevent a situation in which the resources are exceeded.
        :param game_state:
        :param possible_moves:
        :return:
        """
        self.clock = time.process_time()
        # updating the time for the current move according tot he partial amount.
        self.time_for_current_move = self.time_remaining_in_round / self.partial_amount
        # increasing the partial amount.
        if len(possible_moves) == 1:
            if self.turns_remaining_in_round == 1:
                """
                If that is the last turn in the round, we reset the turns and the time counters. As well the partial
                amount to 2.
                """
                self.turns_remaining_in_round = self.k
                self.time_remaining_in_round = self.time_per_k_turns
                # restart the partial amount to 2.
                self.partial_amount = 2
            else:
                # increase the partial amount
                self.partial_amount *= 2
                # decrease remaining turns by 1
                self.turns_remaining_in_round -= 1
                # update the remaining time in the current round
                self.time_remaining_in_round -= (time.process_time() - self.clock)  # Update remaining time
            return possible_moves[0]

        current_depth = 1
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything
        minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time,
                                              self.selective_deepening_criterion)

        # Iterative deepening until the time runs out.
        while True:

            print('going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}'.format(
                current_depth,
                self.time_for_current_move - (time.process_time() - self.clock),
                prev_alpha,
                best_move))

            try:
                (alpha, move), run_time = run_with_limited_time(
                    minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {},
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
            # initializing the time,turns and partial amount.
            self.partial_amount = 2
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            # updating the partial amount, the remaining turns and time.
            self.partial_amount *= 2
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.process_time() - self.clock)
        return best_move

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'improved')

# c:\python35\python.exe run_game.py 3 3 3 y simple_player random_player
