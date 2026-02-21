"""Player hand management."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from hk_mahjong.core.meld import Meld, MeldType
from hk_mahjong.core.tiles import Tile, sort_tiles


@dataclass
class Hand:
    """A player's hand: concealed tiles + exposed melds + bonus tiles."""

    concealed: list[Tile] = field(default_factory=list)
    melds: list[Meld] = field(default_factory=list)
    bonus: list[Tile] = field(default_factory=list)

    @property
    def all_tiles(self) -> list[Tile]:
        """All tiles in the hand including melds (for scoring)."""
        tiles = list(self.concealed)
        for meld in self.melds:
            tiles.extend(meld.tiles)
        return tiles

    @property
    def sorted_concealed(self) -> list[Tile]:
        return sort_tiles(self.concealed)

    def tile_count(self, tile: Tile) -> int:
        """Count how many copies of a tile are in concealed hand."""
        return self.concealed.count(tile)

    def add(self, tile: Tile) -> None:
        self.concealed.append(tile)

    def remove(self, tile: Tile) -> None:
        self.concealed.remove(tile)

    def add_bonus(self, tile: Tile) -> None:
        self.bonus.append(tile)

    def can_chow(self, tile: Tile) -> list[tuple[Tile, Tile]]:
        """Return list of (companion1, companion2) pairs that form chows with tile.

        Only suited tiles can form chows.
        """
        if not tile.is_suited:
            return []
        assert tile.suit is not None
        counts = Counter(t for t in self.concealed if t.suit == tile.suit)
        results: list[tuple[Tile, Tile]] = []
        rank = tile.rank
        suit = tile.suit

        from hk_mahjong.core.tiles import make_suited

        # tile is lowest: tile, tile+1, tile+2
        if rank <= 7:
            t1 = make_suited(suit, rank + 1)
            t2 = make_suited(suit, rank + 2)
            if counts[t1] >= 1 and counts[t2] >= 1:
                results.append((t1, t2))
        # tile is middle: tile-1, tile, tile+1
        if 2 <= rank <= 8:
            t1 = make_suited(suit, rank - 1)
            t2 = make_suited(suit, rank + 1)
            if counts[t1] >= 1 and counts[t2] >= 1:
                results.append((t1, t2))
        # tile is highest: tile-2, tile-1, tile
        if rank >= 3:
            t1 = make_suited(suit, rank - 2)
            t2 = make_suited(suit, rank - 1)
            if counts[t1] >= 1 and counts[t2] >= 1:
                results.append((t1, t2))
        return results

    def can_pong(self, tile: Tile) -> bool:
        """Check if hand can pong (has 2+ copies of tile in concealed)."""
        return self.tile_count(tile) >= 2

    def can_kong(self, tile: Tile) -> bool:
        """Check if hand can kong a discarded tile (has 3 copies in concealed)."""
        return self.tile_count(tile) >= 3

    def can_self_kong(self) -> list[Tile]:
        """Return tiles that can be declared as kong from concealed hand.

        Two cases:
        1. 4 identical tiles in concealed (concealed kong)
        2. Drawn tile matches an existing exposed pong (promote to kong)
        """
        result: list[Tile] = []
        counts = Counter(self.concealed)
        # Case 1: 4 in concealed
        for tile, count in counts.items():
            if count == 4:
                result.append(tile)
        # Case 2: promote existing pong
        for meld in self.melds:
            if meld.meld_type == MeldType.PONG:
                if counts[meld.first_tile] >= 1:
                    result.append(meld.first_tile)
        return result

    def declare_pong(self, tile: Tile) -> Meld:
        """Remove 2 copies from concealed and create exposed pong."""
        for _ in range(2):
            self.concealed.remove(tile)
        meld = Meld(MeldType.PONG, (tile, tile, tile))
        self.melds.append(meld)
        return meld

    def declare_kong(self, tile: Tile) -> Meld:
        """Remove 3 copies from concealed and create exposed kong."""
        for _ in range(3):
            self.concealed.remove(tile)
        meld = Meld(MeldType.KONG, (tile, tile, tile, tile))
        self.melds.append(meld)
        return meld

    def declare_concealed_kong(self, tile: Tile) -> Meld:
        """Remove 4 copies from concealed and create concealed kong."""
        for _ in range(4):
            self.concealed.remove(tile)
        meld = Meld(MeldType.CONCEALED_KONG, (tile, tile, tile, tile))
        self.melds.append(meld)
        return meld

    def promote_kong(self, tile: Tile) -> Meld:
        """Promote an exposed pong to a kong with a tile from concealed."""
        self.concealed.remove(tile)
        # Find and replace the pong
        for i, meld in enumerate(self.melds):
            if meld.meld_type == MeldType.PONG and meld.first_tile == tile:
                new_meld = Meld(MeldType.KONG, (tile, tile, tile, tile))
                self.melds[i] = new_meld
                return new_meld
        raise ValueError(f"No exposed pong of {tile} to promote")

    def declare_chow(self, claimed: Tile, companions: tuple[Tile, Tile]) -> Meld:
        """Remove companions from concealed hand and create chow with claimed tile."""
        for t in companions:
            self.concealed.remove(t)
        from hk_mahjong.core.meld import make_chow
        meld = make_chow(claimed, companions[0], companions[1])
        self.melds.append(meld)
        return meld
