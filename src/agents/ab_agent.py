import time
from agents.base import Agent
from gomoku.board import BLACK, WHITE
from gomoku import rules

try:
    from heuristics.evaluate import evaluate
    from heuristics.evaluate import order_moves
except Exception:
    def evaluate(board, stone, weights=None):
        return 0.0
    def order_moves(board, moves, stone, weights=None):
        return list(moves)

INF = float("inf")

# Transposition table flags:
# after a search we store the result. But alpha beta doesn't always find the
# exact value. sometimes it just proves "at least X" or "at most X".
# These flags record which case we're in so we can use the stored value safely.
# the stored value is the true minimax value for this node
TT_EXACT = 0   
# we got a beta cutoff, so the true value is >= stored value
TT_LOWER = 1   
# no move improved alpha, so the true value is <= stored value
TT_UPPER = 2   

# how many killer moves to remember per depth level
MAX_KILLERS = 2


def _opponent(stone):
    return WHITE if stone == BLACK else BLACK


# Light move ordering:
# used at shallow depths (near leaves) instead of the full order_moves().
# order_moves() simulates opponent responses and builds feature caches which
# is expensive. at depth 1 we are about to call evaluate() anyway, so cheap
# ordering is good enough and saves a lot of time overall.
def _light_order_moves(board, moves, stone):
    """
    Cheap move ordering for leaf and near-leaf nodes.

    Priority:
      1. Immediate wins: always play these first
      2. Immediate blocks: stop the opponent winning
      3. Everything else sorted by manhattan distance to center
         (center squares tend to be more valuable in Gomoku)
    """
    opp = _opponent(stone)
    center = board.size // 2

    wins   = []
    blocks = []
    # list of (distance, move) for sorting
    rest   = []  

    for move in moves:
        # check if this move wins immediately
        b = board.copy()
        b.place(move, stone)
        if rules.winner(b.grid) == stone:
            wins.append(move)
            continue

        # check if skipping this move lets the opponent win immediately
        b2 = board.copy()
        b2.place(move, opp)
        if rules.winner(b2.grid) == opp:
            blocks.append(move)
            continue

        r, c = move
        dist = abs(r - center) + abs(c - center)
        rest.append((dist, move))
    # closest to center first
    rest.sort()  
    return wins + blocks + [m for _, m in rest]


class AlphaBetaAgent(Agent):
    """
    Alpha Beta pruning agent for Gomoku using traditional minimax + iterative deepening.

    Board interface used
    --------------------
    board.legal_moves()       - list[(r, c)]
    board.copy()              - Board          (deep copy)
    board.place(move, stone)  - bool
    board.grid                - tuple[tuple]   (immutable snapshot)

    Plugin hooks (from heuristics/evaluate.py)
    -------------------------------------------
    evaluate(board, stone, weights)   - heuristic shared with RL agent
    order_moves(board, moves, stone)  - move ordering to maximise pruning

    Budget controls
    ---------------
    max_depth        : hard depth limit for iterative deepening
    node_budget      : max nodes expanded per select_move call
    time_budget_ms   : max wall-clock ms per select_move call

    New optimizations (added)
    -------------------------
    light_order_depth : use cheap ordering at this depth or below (default 1)
    tt_max_size       : cap TT entries to avoid memory blowup (default 200_000)
    """

    name = "alphabeta"

    def __init__(
        self,
        max_depth: int = 2,
        node_budget: int = 5_000,
        time_budget_ms: int = 200,
        weights=None,
        # ADDED: at this depth and below, use _light_order_moves instead of
        # the full order_moves() to avoid spending more time ordering than searching
        light_order_depth: int = 1,
        # ADDED: max TT entries. without a cap the table can eat a lot of RAM
        # in long games or high depth searches
        tt_max_size: int = 200_000,
    ):
        self.max_depth = max_depth
        self.node_budget = node_budget
        self.time_budget_ms = time_budget_ms
        self.weights = weights
        #ADDED: new parameters for optimizations
        self.light_order_depth = light_order_depth 
        #ADDED: store the TT size limit as an instance variable so we can check it during the search
        self.tt_max_size = tt_max_size     

        self._nodes: int = 0
        self._t0: float = 0.0

        # ADDED: Transposition Table
        # key   : (board.grid, current_turn), board.grid is already a tuple[tuple] 
        # so it's immutable and hashable, good for dict keys.
        # value : (depth, value, flag)
        #   depth is how many plies were searched below this node
        #   value is the result of that search
        #   flag  is TT_EXACT / TT_LOWER / TT_UPPER (see top of file)
        self._tt: dict = {}

        # ADDED: Killer Move Table
        # key   : depth (int, distance from root)
        # value : list of up to MAX_KILLERS moves that caused beta cutoffs here
        # killers are reset each select_move call because a new search starts.
        self._killers: dict = {}

    # Public interface:

    def select_move(self, board, stone):
        """
        Return the best legal move found within budget. Always returns something.

        Uses iterative deepening: search depth 1, then 2, then 3, etc until we run out of time or nodes. 
        Each completed depth gives us a best move, so if the budget runs out mid-search, we always have a complete
        best move from the last finished depth.
        """
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        self._nodes = 0
        self._t0 = time.time()

        # ADDED: clear TT and killers at the start of each move decision.
        # the TT from a previous turn is mostly stale (the board has changed),
        # and killers from a different position won't be relevant.
        self._tt.clear()
        self._killers.clear()

        # first move from ordered list in case budget expires immediately
        best_move = order_moves(board, moves, stone, self.weights)[0]

        for depth in range(1, self.max_depth + 1):
            move, _ = self._search_root(board, stone, depth)
            if move is not None:
                best_move = move
            if not self._budget_ok():
                break

        return best_move

    # budget helpers:

    def _time_exceeded(self) -> bool:
        """Check if wall clock time limit has been reached."""
        return (time.time() - self._t0) * 1_000.0 >= float(self.time_budget_ms)

    def _node_exceeded(self) -> bool:
        """Check if node expansion limit has been reached."""
        return self._nodes >= int(self.node_budget)

    def _budget_ok(self) -> bool:
        """Return True if both time and node budgets are still available."""
        return not self._time_exceeded() and not self._node_exceeded()

    # killer move helpers:

    # ADDED
    def _record_killer(self, depth: int, move) -> None:
        """
        Store a move that caused a beta cutoff at this depth.

        keep a short list (MAX_KILLERS) per depth. If the move is already
        in the list we don't add a duplicate. When the list is full we drop
        the oldest entry to make room for the new one (FIFO rotation).
        """
        killers = self._killers.setdefault(depth, [])
        if move in killers:
            # already tracked, nothing to do
            return  
        if len(killers) >= MAX_KILLERS:
            # drop oldest killer to stay within the limit
            killers.pop(0)  
        killers.append(move)

    # ADDED
    def _get_killers(self, depth: int) -> list:
        """Return the stored killer moves for this depth (may be empty)."""
        return self._killers.get(depth, [])

    # Search:

    def _search_root(self, board, stone, depth: int):
        """
        Root level search. Returns (best_move, best_value).

        Separated from _search_value so we can track which move
        led to the best score. the recursive function only returns values.

        stone is treated as the maximizing player (root_stone) throughout
        the entire search tree.
        """
        best_move, best_val = None, -INF
        alpha, beta = -INF, INF

        for move in order_moves(board, board.legal_moves(), stone, self.weights):
            child = board.copy()
            child.place(move, stone)

            # Root is always the maximizing player, so opponent goes next (minimizing)
            val = self._search_value(
                board=child,
                root_stone=stone,
                current_turn=_opponent(stone),
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
                # ADDED: root is at ply 0, children are at ply 1
                ply=1,
            )

            if val > best_val:
                best_val, best_move = val, move

            alpha = max(alpha, best_val)

            if not self._budget_ok():
                break

        return best_move, best_val

    def _search_value(
        self,
        board,
        root_stone,
        current_turn,
        depth: int,
        alpha: float,
        beta: float,
        # ADDED: distance from root, used to index the killer table
        ply: int = 0,   
    ) -> float:
        """
        Recursive minimax alpha-beta value function.

        root_stone  : the agent's stone. we always evaluate from this perspective
        current_turn: whose turn it is at this node (may differ from root_stone)

        When current_turn == root_stone  -> maximizing node (we want the highest score)
        When current_turn != root_stone  -> minimizing node (opponent wants lowest score)

        Alpha-beta pruning:
        alpha = best score root_stone is guaranteed so far
        beta  = best score opponent is guaranteed so far
        If alpha >= beta, we prune. the opponent would never let us reach this branch.
        """
        self._nodes += 1

        # ADDED: Transposition table lookup
        # before doing any work, check if we have already searched this exact
        # position at equal or greater depth. If so, we can reuse the result.
        tt_key = (board.grid, current_turn)
        tt_hit = self._tt.get(tt_key)

        if tt_hit is not None:
            tt_depth, tt_val, tt_flag = tt_hit

            # only use the cached result if it was searched at least as deeply
            # as we need right now. A shallower cached result might miss threats
            # that only show up at greater depth.
            if tt_depth >= depth:
                if tt_flag == TT_EXACT:
                    # we know the true value, return it directly
                    return tt_val
                elif tt_flag == TT_LOWER:
                    # this is a lower bound. tighten alpha
                    alpha = max(alpha, tt_val)
                elif tt_flag == TT_UPPER:
                    # this is an upper bound. tighten beta
                    beta = min(beta, tt_val)

                # after adjusting alpha/beta, check if we can prune already
                if alpha >= beta:
                    return tt_val

        # base cases: terminal state, depth limit, or budget exhausted
        if rules.is_terminal(board.grid) or depth == 0 or not self._budget_ok():
            # always evaluate from root_stone's perspective for consistency
            return evaluate(board, root_stone, self.weights)

        # ADDED: choose move ordering strategy based on depth 
        # at leaves and near leaves the full order_moves() costs more than it
        # saves because there are few nodes below to prune. Use the cheap
        # version instead.
        raw_moves = board.legal_moves()

        if depth <= self.light_order_depth:
            ordered = _light_order_moves(board, raw_moves, current_turn)
        else:
            ordered = order_moves(board, raw_moves, current_turn, self.weights)

        # ADDED: inject killer moves near the front of the list 
        # killers are moves that caused beta cutoffs at this ply before.
        # they are not guaranteed to be good here, but they often are, so
        # trying them early can trigger more pruning without extra board copies.
        killers = self._get_killers(ply)
        if killers:
            killer_set = set(killers)
            # find where the win/block priority prefix ends.
            # order_moves puts wins and blocks at the front — killers go after those,
            # not before them.
            split = 0
            for m in ordered:
                b = board.copy()
                b.place(m, current_turn)
                if rules.winner(b.grid) == current_turn:
                    split += 1
                else:
                    b2 = board.copy()
                    b2.place(m, _opponent(current_turn))
                    if rules.winner(b2.grid) == _opponent(current_turn):
                        split += 1
                    else:
                        break

            prefix = ordered[:split]
            remainder = ordered[split:]
            killer_front = [m for m in remainder if m in killer_set]
            killer_rest  = [m for m in remainder if m not in killer_set]
            ordered = prefix + killer_front + killer_rest

        # ADDED: save original alpha and beta before the loop so TT flags are correct.
        # beta can be modified inside the minimizing loop, so we need the original.
        alpha_orig = alpha
        beta_orig = beta

        if current_turn == root_stone:
            # Maximizing player 
            value = -INF
            for move in ordered:
                child = board.copy()
                child.place(move, current_turn)
                val = self._search_value(
                    board=child,
                    root_stone=root_stone,
                    current_turn=_opponent(current_turn),
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                    ply=ply + 1,  # ADDED
                )
                value = max(value, val)
                alpha = max(alpha, value)
                if alpha >= beta:
                    # beta cutoff. opponent won't allow this branch to be reached.
                    # ADDED: record this move as a killer for this ply
                    self._record_killer(ply, move)
                    break
        else:
            # Minimizing player (opponent)
            value = INF
            for move in ordered:
                child = board.copy()
                child.place(move, current_turn)
                val = self._search_value(
                    board=child,
                    root_stone=root_stone,
                    current_turn=_opponent(current_turn),
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                    # ADDED
                    ply=ply + 1,  
                )
                value = min(value, val)
                beta = min(beta, value)
                if alpha >= beta:
                    # alpha cutoff. we already have a better option.
                    # ADDED: record this move as a killer for this ply
                    self._record_killer(ply, move)
                    break

        #ADDED:store result in transposition table
        # only store if the TT is not full, to prevent memory blowup.
        if len(self._tt) < self.tt_max_size:
            # determine the correct flag based on how alpha/beta moved
            if value <= alpha_orig:
                # no move improved alpha. this is an upper bound
                flag = TT_UPPER
            elif value >= beta:
                # we got a cutoff. this is a lower bound
                flag = TT_LOWER
            else:
                # alpha < value < beta. this is exact
                flag = TT_EXACT

            # only overwrite a TT entry if our new search is at least as deep
            existing = self._tt.get(tt_key)
            if existing is None or depth >= existing[0]:
                self._tt[tt_key] = (depth, value, flag)


        return value