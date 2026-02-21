"""Tile definitions for Hong Kong mahjong."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto


class Suit(Enum):
    BAMBOO = auto()
    CHARACTERS = auto()
    DOTS = auto()


class Wind(Enum):
    EAST = auto()
    SOUTH = auto()
    WEST = auto()
    NORTH = auto()


WIND_ORDER = [Wind.EAST, Wind.SOUTH, Wind.WEST, Wind.NORTH]


class Dragon(Enum):
    RED = auto()
    GREEN = auto()
    WHITE = auto()


class BonusType(Enum):
    FLOWER = auto()
    SEASON = auto()


@dataclass(frozen=True, order=True)
class Tile:
    """A single mahjong tile.

    Exactly one of (suit+rank), wind, dragon, or bonus_type should be set.
    """

    suit: Suit | None = None
    rank: int = 0  # 1-9 for suited tiles
    wind: Wind | None = None
    dragon: Dragon | None = None
    bonus_type: BonusType | None = None
    bonus_number: int = 0  # 1-4 for flowers/seasons

    def __post_init__(self) -> None:
        if self.suit is not None:
            if not 1 <= self.rank <= 9:
                raise ValueError(f"Suited tile rank must be 1-9, got {self.rank}")
        elif self.wind is not None:
            pass
        elif self.dragon is not None:
            pass
        elif self.bonus_type is not None:
            if not 1 <= self.bonus_number <= 4:
                raise ValueError(f"Bonus number must be 1-4, got {self.bonus_number}")
        else:
            raise ValueError("Tile must have suit, wind, dragon, or bonus_type set")

    @property
    def is_suited(self) -> bool:
        return self.suit is not None

    @property
    def is_honor(self) -> bool:
        return self.wind is not None or self.dragon is not None

    @property
    def is_terminal(self) -> bool:
        return self.is_suited and self.rank in (1, 9)

    @property
    def is_terminal_or_honor(self) -> bool:
        return self.is_terminal or self.is_honor

    @property
    def is_bonus(self) -> bool:
        return self.bonus_type is not None

    @property
    def is_simple(self) -> bool:
        return self.is_suited and 2 <= self.rank <= 8

    @property
    def sort_key(self) -> tuple[int, int, int, int]:
        """Key for sorting tiles in display order."""
        if self.suit is not None:
            return (0, self.suit.value, self.rank, 0)
        if self.wind is not None:
            return (1, self.wind.value, 0, 0)
        if self.dragon is not None:
            return (2, self.dragon.value, 0, 0)
        # bonus
        assert self.bonus_type is not None
        return (3, self.bonus_type.value, self.bonus_number, 0)

    def short_name(self) -> str:
        """Short human-readable name, e.g. '3B', 'EW', 'RD', 'F1'."""
        if self.suit is not None:
            suffix = {Suit.BAMBOO: "B", Suit.CHARACTERS: "C", Suit.DOTS: "D"}
            return f"{self.rank}{suffix[self.suit]}"
        if self.wind is not None:
            return {Wind.EAST: "EW", Wind.SOUTH: "SW", Wind.WEST: "WW", Wind.NORTH: "NW"}[self.wind]
        if self.dragon is not None:
            return {Dragon.RED: "RD", Dragon.GREEN: "GD", Dragon.WHITE: "WD"}[self.dragon]
        assert self.bonus_type is not None
        prefix = {BonusType.FLOWER: "F", BonusType.SEASON: "S"}
        return f"{prefix[self.bonus_type]}{self.bonus_number}"

    def __repr__(self) -> str:
        return f"Tile({self.short_name()})"


def make_suited(suit: Suit, rank: int) -> Tile:
    return Tile(suit=suit, rank=rank)


def make_wind(wind: Wind) -> Tile:
    return Tile(wind=wind)


def make_dragon(dragon: Dragon) -> Tile:
    return Tile(dragon=dragon)


def make_bonus(bonus_type: BonusType, number: int) -> Tile:
    return Tile(bonus_type=bonus_type, bonus_number=number)


def create_full_tileset() -> list[Tile]:
    """Create the complete 144-tile HK mahjong set."""
    tiles: list[Tile] = []

    # 4 copies of each suited tile (3 suits × 9 ranks × 4 = 108)
    for suit in Suit:
        for rank in range(1, 10):
            for _ in range(4):
                tiles.append(make_suited(suit, rank))

    # 4 copies of each wind (4 × 4 = 16)
    for wind in Wind:
        for _ in range(4):
            tiles.append(make_wind(wind))

    # 4 copies of each dragon (3 × 4 = 12)
    for dragon in Dragon:
        for _ in range(4):
            tiles.append(make_dragon(dragon))

    # 1 copy of each flower (4) and each season (4) = 8
    for bonus_type in BonusType:
        for num in range(1, 5):
            tiles.append(make_bonus(bonus_type, num))

    return tiles


def sort_tiles(tiles: Sequence[Tile]) -> list[Tile]:
    """Return tiles sorted in standard display order."""
    return sorted(tiles, key=lambda t: t.sort_key)


# Commonly used tile constants for convenience
ALL_TERMINALS_AND_HONORS: frozenset[Tile] = frozenset(
    [make_suited(s, r) for s in Suit for r in (1, 9)]
    + [make_wind(w) for w in Wind]
    + [make_dragon(d) for d in Dragon]
)
