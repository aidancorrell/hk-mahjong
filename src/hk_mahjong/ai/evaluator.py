"""Shanten calculation and tile utility evaluation."""

from __future__ import annotations

from collections import Counter

from hk_mahjong.core.meld import Meld
from hk_mahjong.core.tiles import Suit, Tile, make_suited


def calculate_shanten(concealed: list[Tile], melds: list[Meld]) -> int:
    """Calculate shanten number (distance to tenpai).

    shanten = 0 means tenpai (one tile away from winning)
    shanten = -1 means already a winning hand
    shanten = 8 means worst case (no progress)

    Uses a simplified approach: count pairs, partial melds, complete melds.
    """
    from hk_mahjong.core.win_check import check_win

    # Already winning?
    if check_win(concealed, melds):
        return -1

    needed_melds = 4 - len(melds)
    counts = Counter(concealed)

    # Use a greedy estimation approach
    best = _estimate_shanten(counts, needed_melds)
    return best


def _estimate_shanten(counts: Counter[Tile], needed_melds: int) -> int:
    """Estimate shanten by counting useful tile groups."""
    remaining = Counter(counts)
    complete = 0  # complete melds found
    partial = 0   # pairs/partial sequences
    has_pair = False

    # First pass: find complete melds (triplets and sequences)
    tiles_by_suit: dict[Suit | None, list[Tile]] = {}
    for tile in remaining:
        key = tile.suit if tile.is_suited else None
        tiles_by_suit.setdefault(key, []).append(tile)

    work = Counter(remaining)

    # Count triplets
    for tile, count in list(work.items()):
        while work[tile] >= 3 and complete < needed_melds:
            work[tile] -= 3
            complete += 1

    # Count sequences
    for suit in Suit:
        for rank in range(1, 8):
            t1 = make_suited(suit, rank)
            t2 = make_suited(suit, rank + 1)
            t3 = make_suited(suit, rank + 2)
            while (work.get(t1, 0) >= 1 and work.get(t2, 0) >= 1
                   and work.get(t3, 0) >= 1 and complete < needed_melds):
                work[t1] -= 1
                work[t2] -= 1
                work[t3] -= 1
                complete += 1

    # Count pairs and partial sequences
    for tile, count in list(work.items()):
        if count >= 2 and not has_pair:
            has_pair = True
            work[tile] -= 2

    for tile, count in list(work.items()):
        while work[tile] >= 2 and partial < (needed_melds - complete):
            work[tile] -= 2
            partial += 1

    # Partial sequences
    for suit in Suit:
        for rank in range(1, 9):
            t1 = make_suited(suit, rank)
            t2 = make_suited(suit, rank + 1)
            if (work.get(t1, 0) >= 1 and work.get(t2, 0) >= 1
                    and partial < (needed_melds - complete)):
                work[t1] -= 1
                work[t2] -= 1
                partial += 1

    # Shanten formula: 2 * needed - 2 * complete - partial - (1 if has_pair)
    shanten = 2 * needed_melds - 2 * complete - partial - (1 if has_pair else 0)
    is_complete = complete == needed_melds and has_pair
    return max(shanten, 0) if not is_complete else max(shanten, 0)


def tile_danger_score(tile: Tile, all_discards: list[list[Tile]]) -> float:
    """Estimate how 'dangerous' a tile is to discard.

    Lower score = safer to discard.
    Tiles already discarded by others are safer.
    """
    total_discarded = sum(d.count(tile) for d in all_discards)
    # More copies already out = safer
    safety = total_discarded * 2.0

    # Terminal/honor tiles are generally safer mid-game
    if tile.is_terminal_or_honor:
        safety += 0.5

    return -safety  # negative = lower danger


def tile_utility(tile: Tile, hand_tiles: list[Tile]) -> float:
    """Estimate how useful a tile is to keep.

    Higher = more useful (contributes to melds).
    """
    counts = Counter(hand_tiles)
    score = 0.0

    # Pairs and triplets
    c = counts[tile]
    score += c * 2.0

    # Adjacency (for suited tiles)
    if tile.is_suited:
        assert tile.suit is not None
        for delta in (-2, -1, 1, 2):
            r = tile.rank + delta
            if 1 <= r <= 9:
                neighbor = make_suited(tile.suit, r)
                if counts[neighbor] > 0:
                    score += 1.5 if abs(delta) == 1 else 0.5

    return score
