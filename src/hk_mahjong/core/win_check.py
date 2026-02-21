"""Win detection via backtracking hand decomposition."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from hk_mahjong.core.meld import Meld, MeldType
from hk_mahjong.core.tiles import (
    ALL_TERMINALS_AND_HONORS,
    Tile,
    make_suited,
)


@dataclass(frozen=True)
class HandDecomposition:
    """A valid winning decomposition of a hand."""

    melds: tuple[Meld, ...]  # 4 melds (from concealed decomposition + exposed)
    pair: Tile
    concealed_melds: tuple[Meld, ...]  # only the melds from concealed tiles


def is_thirteen_orphans(concealed: list[Tile], melds: list[Meld]) -> Tile | None:
    """Check for Thirteen Orphans (十三幺).

    Must have no exposed melds and one each of all terminals/honors + one duplicate.
    Returns the pair tile if valid, else None.
    """
    if melds:
        return None
    if len(concealed) != 14:
        return None

    required = set(ALL_TERMINALS_AND_HONORS)
    counts = Counter(concealed)

    # Must have at least one of each required tile
    for t in required:
        if counts[t] < 1:
            return None

    # Exactly one tile appears twice (the pair)
    pair_tile: Tile | None = None
    for t in required:
        if counts[t] == 2:
            pair_tile = t
            break

    # Total should be exactly 14 tiles, all from required set
    if sum(counts[t] for t in required) != 14:
        return None

    return pair_tile


def find_winning_decompositions(
    concealed: list[Tile], exposed_melds: list[Meld]
) -> list[HandDecomposition]:
    """Find all valid 4-melds + 1-pair decompositions.

    concealed: the tiles in the player's concealed hand (should be 14 - 3*exposed)
    exposed_melds: already declared melds

    A winning hand is: 4 melds + 1 pair, where melds come from
    exposed_melds + decomposed concealed tiles.
    """
    needed_melds = 4 - len(exposed_melds)
    # For standard win: concealed should have 3*needed_melds + 2 tiles
    expected = 3 * needed_melds + 2
    if len(concealed) != expected:
        return []

    results: list[HandDecomposition] = []
    counts = Counter(concealed)

    def _backtrack(
        remaining: Counter[Tile],
        found_melds: list[Meld],
        pair: Tile | None,
    ) -> None:
        total_left = sum(remaining.values())

        if total_left == 0 and pair is not None and len(found_melds) == needed_melds:
            decomp = HandDecomposition(
                melds=tuple(list(exposed_melds) + found_melds),
                pair=pair,
                concealed_melds=tuple(found_melds),
            )
            results.append(decomp)
            return

        if total_left == 0:
            return

        # Pick the smallest tile to process (ensures consistent ordering)
        min_tile = min(remaining.keys(), key=lambda t: t.sort_key)

        # Try using min_tile as pair (if no pair yet)
        if pair is None and remaining[min_tile] >= 2:
            remaining[min_tile] -= 2
            if remaining[min_tile] == 0:
                del remaining[min_tile]
            _backtrack(remaining, found_melds, min_tile)
            remaining[min_tile] = remaining.get(min_tile, 0) + 2

        if len(found_melds) < needed_melds:
            # Try pong with min_tile
            if remaining[min_tile] >= 3:
                remaining[min_tile] -= 3
                if remaining[min_tile] == 0:
                    del remaining[min_tile]
                meld = Meld(MeldType.PONG, (min_tile, min_tile, min_tile))
                found_melds.append(meld)
                _backtrack(remaining, found_melds, pair)
                found_melds.pop()
                remaining[min_tile] = remaining.get(min_tile, 0) + 3

            # Try chow with min_tile as lowest
            if min_tile.is_suited and min_tile.rank <= 7:
                assert min_tile.suit is not None
                t2 = make_suited(min_tile.suit, min_tile.rank + 1)
                t3 = make_suited(min_tile.suit, min_tile.rank + 2)
                if remaining.get(t2, 0) >= 1 and remaining.get(t3, 0) >= 1:
                    remaining[min_tile] -= 1
                    if remaining[min_tile] == 0:
                        del remaining[min_tile]
                    remaining[t2] -= 1
                    if remaining[t2] == 0:
                        del remaining[t2]
                    remaining[t3] -= 1
                    if remaining[t3] == 0:
                        del remaining[t3]
                    meld = Meld(MeldType.CHOW, (min_tile, t2, t3))
                    found_melds.append(meld)
                    _backtrack(remaining, found_melds, pair)
                    found_melds.pop()
                    remaining[min_tile] = remaining.get(min_tile, 0) + 1
                    remaining[t2] = remaining.get(t2, 0) + 1
                    remaining[t3] = remaining.get(t3, 0) + 1

    _backtrack(Counter(counts), [], None)
    return results


def check_win(concealed: list[Tile], exposed_melds: list[Meld]) -> list[HandDecomposition]:
    """Check if a hand is a winning hand. Returns all valid decompositions.

    Also checks for special hands like Thirteen Orphans.
    """
    results = find_winning_decompositions(concealed, exposed_melds)

    # Check Thirteen Orphans
    orphan_pair = is_thirteen_orphans(concealed, exposed_melds)
    if orphan_pair is not None:
        results.append(
            HandDecomposition(
                melds=(),
                pair=orphan_pair,
                concealed_melds=(),
            )
        )

    return results
