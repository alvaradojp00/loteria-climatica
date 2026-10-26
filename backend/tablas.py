"""Playing boards (tablas) and the printable deck.

A lotería tabla is a 4x4 grid of sixteen cards drawn from the deck. Real
tablas have to differ from each other or the game is no fun, so boards are
generated from a seed and checked for overlap rather than drawn blindly.

Deterministic -- a seed gives the same six boards every time, which means a
printed set can be reproduced.
"""

from __future__ import annotations

import random

ROWS, COLS = 4, 4
PER_BOARD = ROWS * COLS
MAX_SHARED = 6          # two boards may share at most this many cards


def _too_similar(board: list[str], others: list[list[str]]) -> bool:
    s = set(board)
    return any(len(s & set(o)) > MAX_SHARED for o in others)


def generate(card_ids: list[str], count: int = 6, seed: int | None = None
             ) -> dict:
    """Build `count` tablas of 16 cards each."""
    if len(card_ids) < PER_BOARD:
        raise ValueError(f"need at least {PER_BOARD} cards, have {len(card_ids)}")

    if seed is None:
        seed = random.randrange(1, 10_000_000)
    rng = random.Random(seed)

    boards: list[list[str]] = []
    for _ in range(count):
        for _attempt in range(400):
            pick = rng.sample(card_ids, PER_BOARD)
            if not _too_similar(pick, boards):
                boards.append(pick)
                break
        else:
            # deck too small to keep boards distinct; accept the overlap
            boards.append(rng.sample(card_ids, PER_BOARD))

    return {
        "seed": seed,
        "rows": ROWS,
        "cols": COLS,
        "count": len(boards),
        "boards": [
            {"n": i + 1, "cards": b, "grid": [b[r * COLS:(r + 1) * COLS] for r in range(ROWS)]}
            for i, b in enumerate(boards)
        ],
    }


def call_order(card_ids: list[str], seed: int | None = None) -> dict:
    """The shuffled order a caller (el gritón) reads the deck in."""
    if seed is None:
        seed = random.randrange(1, 10_000_000)
    rng = random.Random(seed)
    order = card_ids[:]
    rng.shuffle(order)
    return {"seed": seed, "order": order}
