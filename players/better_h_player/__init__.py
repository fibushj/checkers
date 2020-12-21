
#===============================================================================
# Imports
#===============================================================================

from players import simple_player
import abstract
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP
import time
from collections import defaultdict

#===============================================================================
# Globals
#===============================================================================

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5

#===============================================================================
# Player
#===============================================================================

class Player(simple_player.Player):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        simple_player.Player.__init__(self, setup_time, player_color, time_per_k_turns, k)
        


    def utility(self, state):
        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY
        if state.turns_since_last_jump >= MAX_TURNS_NO_JUMP:
            return 0

        piece_counts = defaultdict(lambda: 0)
        for loc_val in state.board.values():
            if loc_val != EM:
                piece_counts[loc_val] += 1
        
        opponent_color = OPPONENT_COLOR[self.color]
        
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
            return my_u - op_u
        
    def selective_deepening_criterion(self, state):
        # Simple player does not selectively deepen into certain nodes.
        return False

    
