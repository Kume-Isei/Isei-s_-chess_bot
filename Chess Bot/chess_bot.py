"""Name: Isei Okhakume Paul
Project: Chess Bot
"""

import sys
import time
import argparse
import chess

# --------------------------------------------------------------------------
# Piece values and piece-square tables
# --------------------------------------------------------------------------

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Tables are given from White's perspective, a8=index 0 ... h1=index 63.
PAWN_TABLE = [
      0,   0,   0,   0,   0,   0,   0,   0,
     50,  50,  50,  50,  50,  50,  50,  50,
     10,  10,  20,  30,  30,  20,  10,  10,
      5,   5,  10,  25,  25,  10,   5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      5,  -5, -10,   0,   0, -10,  -5,   5,
      5,  10,  10, -20, -20,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_TABLE = [
      0,   0,   0,   0,   0,   0,   0,   0,
      5,  10,  10,  10,  10,  10,  10,   5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
      0,   0,   0,   5,   5,   0,   0,   0,
]

QUEEN_TABLE = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_MID_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
]

KING_END_TABLE = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]

TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
}

CHECKMATE_SCORE = 1_000_000


def _table_index(square: int, color: bool) -> int:
    """Convert a chess.Square into an index into our (White-oriented) tables."""
    if color == chess.WHITE:
        rank = 7 - chess.square_rank(square)
        file = chess.square_file(square)
    else:
        rank = chess.square_rank(square)
        file = chess.square_file(square)
    return rank * 8 + file


def game_phase(board: chess.Board) -> float:
    """Returns 1.0 for full midgame material, 0.0 for bare-bones endgame."""
    phase_weights = {
        chess.KNIGHT: 1, chess.BISHOP: 1, chess.ROOK: 2, chess.QUEEN: 4
    }
    max_phase = 24  # 4 knights+bishops*1 + 4 rooks*2 + 2 queens*4 = 4+4+8+8=24
    phase = 0
    for piece_type, weight in phase_weights.items():
        phase += weight * len(board.pieces(piece_type, chess.WHITE))
        phase += weight * len(board.pieces(piece_type, chess.BLACK))
    return min(phase / max_phase, 1.0)


def evaluate(board: chess.Board) -> int:
    """Static evaluation from the perspective of the side to move (negamax convention)."""
    if board.is_checkmate():
        return -CHECKMATE_SCORE
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    phase = game_phase(board)
    score = 0

    for square, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        idx = _table_index(square, piece.color)

        if piece.piece_type == chess.KING:
            pst = KING_MID_TABLE[idx] * phase + KING_END_TABLE[idx] * (1 - phase)
        else:
            pst = TABLES[piece.piece_type][idx]

        total = value + pst
        score += total if piece.color == chess.WHITE else -total

    # Mobility (cheap proxy for activity/space)
    mobility_bonus = 2
    turn = board.turn
    score += mobility_bonus * len(list(board.legal_moves)) * (1 if turn == chess.WHITE else -1)
    board.turn = not turn
    score -= mobility_bonus * len(list(board.legal_moves)) * (1 if turn == chess.WHITE else -1)
    board.turn = turn

    return score if board.turn == chess.WHITE else -score


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

EXACT, LOWERBOUND, UPPERBOUND = 0, 1, 2


class Engine:
    def __init__(self):
        self.tt = {}  # zobrist_hash -> (depth, score, flag, best_move)
        self.killers = {}  # depth -> [move, move]
        self.nodes = 0
        self.start_time = 0.0
        self.time_limit = 5.0
        self.stop = False

    def _time_up(self) -> bool:
        return (time.time() - self.start_time) > self.time_limit

    def mvv_lva_score(self, board: chess.Board, move: chess.Move) -> int:
        if not board.is_capture(move):
            return 0
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim is None:  # en passant
            victim_value = PIECE_VALUES[chess.PAWN]
        else:
            victim_value = PIECE_VALUES[victim.piece_type]
        attacker_value = PIECE_VALUES[attacker.piece_type] if attacker else 0
        return 10_000 + victim_value * 10 - attacker_value

    def ordered_moves(self, board: chess.Board, depth: int, tt_move):
        moves = list(board.legal_moves)

        def key(m):
            if tt_move is not None and m == tt_move:
                return 1_000_000
            if board.is_capture(m):
                return self.mvv_lva_score(board, m)
            if m in self.killers.get(depth, []):
                return 500
            return 0

        moves.sort(key=key, reverse=True)
        return moves

    def quiescence(self, board: chess.Board, alpha: int, beta: int) -> int:
        self.nodes += 1
        stand_pat = evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        for move in board.legal_moves:
            if not board.is_capture(move):
                continue
            board.push(move)
            score = -self.quiescence(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int) -> int:
        self.nodes += 1
        if self.nodes % 2048 == 0 and self._time_up():
            self.stop = True

        alpha_orig = alpha
        key = chess.polyglot.zobrist_hash(board)
        tt_entry = self.tt.get(key)
        tt_move = None
        if tt_entry is not None:
            tt_depth, tt_score, tt_flag, tt_move = tt_entry
            if tt_depth >= depth:
                if tt_flag == EXACT:
                    return tt_score
                elif tt_flag == LOWERBOUND:
                    alpha = max(alpha, tt_score)
                elif tt_flag == UPPERBOUND:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        if board.is_checkmate():
            return -CHECKMATE_SCORE + (1000 - depth)  # prefer faster mates
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        if depth == 0:
            return self.quiescence(board, alpha, beta)

        best_score = -CHECKMATE_SCORE * 2
        best_move = None

        for move in self.ordered_moves(board, depth, tt_move):
            board.push(move)
            score = -self.negamax(board, depth - 1, -beta, -alpha)
            board.pop()

            if self.stop:
                return best_score if best_move is not None else 0

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                if not board.is_capture(move):
                    self.killers.setdefault(depth, [])
                    if move not in self.killers[depth]:
                        self.killers[depth].insert(0, move)
                        self.killers[depth] = self.killers[depth][:2]
                break

        flag = EXACT
        if best_score <= alpha_orig:
            flag = UPPERBOUND
        elif best_score >= beta:
            flag = LOWERBOUND
        self.tt[key] = (depth, best_score, flag, best_move)

        return best_score

    def search(self, board: chess.Board, time_limit: float = 5.0, max_depth: int = 64):
        self.start_time = time.time()
        self.time_limit = time_limit
        self.stop = False
        self.nodes = 0

        best_move = None
        best_score = 0

        for depth in range(1, max_depth + 1):
            self.killers.setdefault(depth, [])
            score = self.negamax(board, depth, -CHECKMATE_SCORE * 2, CHECKMATE_SCORE * 2)

            if self.stop:
                break

            key = chess.polyglot.zobrist_hash(board)
            entry = self.tt.get(key)
            if entry is not None and entry[3] is not None:
                best_move = entry[3]
                best_score = score

            elapsed = time.time() - self.start_time
            print(f"info depth {depth} score cp {score} nodes {self.nodes} "
                  f"time {int(elapsed*1000)} pv {best_move}", file=sys.stderr)

            if elapsed > time_limit * 0.6:
                break

        if best_move is None:
            legal = list(board.legal_moves)
            best_move = legal[0] if legal else None

        return best_move, best_score


# --------------------------------------------------------------------------
# CLI play mode
# --------------------------------------------------------------------------

def play_cli(time_limit: float = 3.0):
    board = chess.Board()
    engine = Engine()

    print("You are White. Enter moves in UCI format (e.g. e2e4) or SAN (e.g. Nf3).")
    print("Type 'quit' to exit.\n")

    while not board.is_game_over():
        print(board)
        print()
        if board.turn == chess.WHITE:
            move_str = input("Your move: ").strip()
            if move_str.lower() in ("quit", "exit"):
                break
            try:
                move = board.parse_san(move_str)
            except ValueError:
                try:
                    move = chess.Move.from_uci(move_str)
                    if move not in board.legal_moves:
                        raise ValueError
                except ValueError:
                    print("Illegal or unparseable move, try again.")
                    continue
            board.push(move)
        else:
            print("Engine is thinking...")
            move, score = engine.search(board, time_limit=time_limit)
            print(f"Engine plays: {board.san(move)}  (eval: {score/100:.2f})\n")
            board.push(move)

    print(board)
    print("\nGame over:", board.result())


# --------------------------------------------------------------------------
# UCI mode
# --------------------------------------------------------------------------

def uci_loop():
    board = chess.Board()
    engine = Engine()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if line == "uci":
            print("id name PyNegamaxBot")
            print("id author Claude")
            print("uciok")
        elif line == "isready":
            print("readyok")
        elif line == "ucinewgame":
            board = chess.Board()
            engine = Engine()
        elif line.startswith("position"):
            parts = line.split()
            if "startpos" in parts:
                board = chess.Board()
                if "moves" in parts:
                    moves_idx = parts.index("moves")
                    for m in parts[moves_idx + 1:]:
                        board.push_uci(m)
            elif "fen" in parts:
                fen_idx = parts.index("fen")
                fen = " ".join(parts[fen_idx + 1:fen_idx + 7])
                board = chess.Board(fen)
                if "moves" in parts:
                    moves_idx = parts.index("moves")
                    for m in parts[moves_idx + 1:]:
                        board.push_uci(m)
        elif line.startswith("go"):
            time_limit = 5.0
            parts = line.split()
            # crude time management from wtime/btime if given
            if "wtime" in parts and "btime" in parts:
                wtime = int(parts[parts.index("wtime") + 1])
                btime = int(parts[parts.index("btime") + 1])
                remaining = wtime if board.turn == chess.WHITE else btime
                time_limit = max(0.2, min(5.0, remaining / 30000))
            move, _ = engine.search(board, time_limit=time_limit)
            print(f"bestmove {move.uci() if move else '0000'}")
            sys.stdout.flush()
        elif line == "quit":
            break


if __name__ == "__main__":
    import chess.polyglot  # noqa: E402 (needed for zobrist hashing)

    parser = argparse.ArgumentParser(description="A simple negamax chess engine.")
    parser.add_argument("--uci", action="store_true", help="Run as a UCI engine")
    parser.add_argument("--time", type=float, default=3.0, help="Seconds per engine move (CLI mode)")
    args = parser.parse_args()

    if args.uci:
        uci_loop()
    else:
        play_cli(time_limit=args.time)
