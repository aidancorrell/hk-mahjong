"""Meld types and validation for mahjong."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from hk_mahjong.core.tiles import Tile


class MeldType(Enum):
    CHOW = auto()    # 3 consecutive tiles of same suit
    PONG = auto()    # 3 identical tiles
    KONG = auto()    # 4 identical tiles (exposed)
    CONCEALED_KONG = auto()  # 4 identical tiles (concealed)


@dataclass(frozen=True)
class Meld:
    """A declared meld (exposed or concealed kong)."""

    meld_type: MeldType
    tiles: tuple[Tile, ...]

    def __post_init__(self) -> None:
        _validate_meld(self.meld_type, self.tiles)

    @property
    def is_kong(self) -> bool:
        return self.meld_type in (MeldType.KONG, MeldType.CONCEALED_KONG)

    @property
    def is_concealed(self) -> bool:
        return self.meld_type == MeldType.CONCEALED_KONG

    @property
    def is_pong(self) -> bool:
        return self.meld_type == MeldType.PONG

    @property
    def is_chow(self) -> bool:
        return self.meld_type == MeldType.CHOW

    @property
    def first_tile(self) -> Tile:
        """Representative tile for the meld (lowest for chow, any for pong/kong)."""
        return self.tiles[0]


def _validate_meld(meld_type: MeldType, tiles: tuple[Tile, ...]) -> None:
    if meld_type == MeldType.CHOW:
        if len(tiles) != 3:
            raise ValueError("Chow must have exactly 3 tiles")
        if not all(t.is_suited for t in tiles):
            raise ValueError("Chow tiles must all be suited")
        suits = {t.suit for t in tiles}
        if len(suits) != 1:
            raise ValueError("Chow tiles must be the same suit")
        ranks = sorted(t.rank for t in tiles)
        if ranks[1] - ranks[0] != 1 or ranks[2] - ranks[1] != 1:
            raise ValueError("Chow tiles must be consecutive")
    elif meld_type == MeldType.PONG:
        if len(tiles) != 3:
            raise ValueError("Pong must have exactly 3 tiles")
        if tiles[0] != tiles[1] or tiles[1] != tiles[2]:
            raise ValueError("Pong tiles must be identical")
    elif meld_type in (MeldType.KONG, MeldType.CONCEALED_KONG):
        if len(tiles) != 4:
            raise ValueError("Kong must have exactly 4 tiles")
        if not all(t == tiles[0] for t in tiles):
            raise ValueError("Kong tiles must be identical")


def make_chow(t1: Tile, t2: Tile, t3: Tile) -> Meld:
    """Create a chow meld, auto-sorting by rank."""
    sorted_tiles = tuple(sorted([t1, t2, t3], key=lambda t: t.rank))
    return Meld(MeldType.CHOW, sorted_tiles)


def make_pong(tile: Tile) -> Meld:
    return Meld(MeldType.PONG, (tile, tile, tile))


def make_kong(tile: Tile, concealed: bool = False) -> Meld:
    mt = MeldType.CONCEALED_KONG if concealed else MeldType.KONG
    return Meld(mt, (tile, tile, tile, tile))
