def player(prev_play, opponent_history=[]):
    """
    Beats all four freeCodeCamp RPS opponents.

    Two critical fixes vs the naive meta-strategy approach:
      1. MATCH RESET  – prev_play == "" signals the start of a new match.
                        We clear all histories and scores so that state from
                        a previous match (e.g. 1000 Quincy games) never
                        contaminates the next match (e.g. Abbey).
      2. ABBEY SEEDING – abbey-counter gets score=1 at match start so it is
                         the default pick before any evidence accumulates.
                         This prevents us from feeding Abbey's learner with
                         moves produced by the wrong strategy while we wait
                         for scores to diverge.
    """

    beats  = {"R": "P",  "P": "S",  "S": "R"}

    # ── reset at the start of every new match ─────────────────────────────────
    if not prev_play:
        opponent_history.clear()
        player._my_history.clear()
        player._last_preds.clear()
        # Abbey gets a 1-point head start so it is picked before evidence
        # accumulates; the scorer will quickly correct this if wrong.
        player._scores = {
            "quincy": 0, "kris": 0, "abbey": 1,
            "mrugesh": 0, "freq": 0, "p2": 0, "p3": 0,
        }

    my_history = player._my_history
    scores     = player._scores
    last_preds = player._last_preds

    if prev_play:
        opponent_history.append(prev_play)

    n = len(opponent_history)

    # ── score every strategy against what the opponent actually played ─────────
    if prev_play and last_preds:
        for name, predicted_move in last_preds.items():
            if   predicted_move == beats[prev_play]: scores[name] += 2  # win
            elif predicted_move == prev_play:        pass                 # tie
            else:                                    scores[name] -= 1   # loss

    # ── helpers ────────────────────────────────────────────────────────────────
    def counter(m):
        return beats[m]

    # ── strategy: Quincy ───────────────────────────────────────────────────────
    def s_quincy():
        """Quincy cycles R → R → S → P. Index into the cycle and counter it."""
        return counter(["R", "R", "S", "P"][n % 4])

    # ── strategy: Kris ─────────────────────────────────────────────────────────
    def s_kris():
        """
        Kris plays counter(our_last_move).
        We play counter(counter(our_last_move)) to beat that.
        """
        if not my_history:
            return "P"
        return counter(counter(my_history[-1]))

    # ── strategy: Abbey ────────────────────────────────────────────────────────
    def s_abbey():
        """
        Abbey builds a pair-frequency table of OUR consecutive moves
        and predicts our next move based on what most often followed our
        last move; she then plays counter(prediction).

        We replicate her exact table and play counter(abbey_play) to win.

        NOTE: This uses my_history (our move history), NOT opponent_history,
        because Abbey tracks US, not herself.
        """
        if len(my_history) < 2:
            return "P"

        # Replicate Abbey's play_order table for our moves
        play_order = {a + b: 0 for a in "RPS" for b in "RPS"}
        for i in range(len(my_history) - 1):
            play_order[my_history[i] + my_history[i + 1]] += 1

        last_move = my_history[-1]
        # What could follow our last move?
        potential = {last_move + nxt: play_order[last_move + nxt] for nxt in "RPS"}

        # Abbey's prediction of our next move (the move she'll counter)
        abbey_prediction = max(potential, key=potential.get)[-1]
        # What Abbey will play
        abbey_play = counter(abbey_prediction)
        # What beats Abbey
        return counter(abbey_play)

    # ── strategy: Mrugesh ──────────────────────────────────────────────────────
    def s_mrugesh():
        """
        Mrugesh plays counter(most_common move in our last 10).
        We play counter(counter(most_common)) to beat that.
        """
        if len(my_history) < 2:
            return "P"
        last10  = my_history[-10:]
        counts  = {m: last10.count(m) for m in "RPS"}
        return counter(counter(max(counts, key=counts.get)))

    # ── strategy: opponent frequency ───────────────────────────────────────────
    def s_freq():
        """Counter the opponent's most frequent recent move."""
        if n < 3:
            return "P"
        recent = opponent_history[-20:]
        counts = {m: recent.count(m) for m in "RPS"}
        return counter(max(counts, key=counts.get))

    # ── strategy: 2-gram pattern on opponent ───────────────────────────────────
    def s_pattern2():
        """Predict opponent's next move from their most common 2-move sequence."""
        if n < 4:
            return "P"
        table = {}
        for i in range(n - 2):
            key = opponent_history[i] + opponent_history[i + 1]
            nxt = opponent_history[i + 2]
            table.setdefault(key, {"R": 0, "P": 0, "S": 0})
            table[key][nxt] += 1
        key = opponent_history[-2] + opponent_history[-1]
        if key in table:
            return counter(max(table[key], key=table[key].get))
        return "P"

    # ── strategy: 3-gram pattern on opponent ───────────────────────────────────
    def s_pattern3():
        """Same as s_pattern2 but using 3-move sequences."""
        if n < 5:
            return "P"
        table = {}
        for i in range(n - 3):
            key = "".join(opponent_history[i:i + 3])
            nxt = opponent_history[i + 3]
            table.setdefault(key, {"R": 0, "P": 0, "S": 0})
            table[key][nxt] += 1
        key = "".join(opponent_history[-3:])
        if key in table:
            return counter(max(table[key], key=table[key].get))
        return "P"

    # ── generate all predictions for the NEXT round ───────────────────────────
    strategies = {
        "quincy":  s_quincy,
        "kris":    s_kris,
        "abbey":   s_abbey,
        "mrugesh": s_mrugesh,
        "freq":    s_freq,
        "p2":      s_pattern2,
        "p3":      s_pattern3,
    }

    for name, fn in strategies.items():
        last_preds[name] = fn()

    # ── pick the strategy with the highest cumulative score ───────────────────
    best = max(scores, key=scores.get)
    move = last_preds[best]

    my_history.append(move)
    return move


# ── persistent state (survives across calls within a Python session) ──────────
player._my_history  = []
player._last_preds  = {}
player._scores      = {
    "quincy": 0, "kris": 0, "abbey": 1,
    "mrugesh": 0, "freq": 0, "p2": 0, "p3": 0,
}