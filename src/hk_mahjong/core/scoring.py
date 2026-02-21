"""Hong Kong mahjong faan (番) scoring system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from hk_mahjong.core.meld import Meld
from hk_mahjong.core.tiles import (
    BonusType,
    Dragon,
    Tile,
    Wind,
)
from hk_mahjong.core.win_check import HandDecomposition

if TYPE_CHECKING:
    pass

LIMIT_FAAN = 13  # Maximum faan (limit hand)


@dataclass
class ScoringContext:
    """All information needed to score a winning hand."""

    decomposition: HandDecomposition
    exposed_melds: list[Meld]
    concealed_tiles: list[Tile]
    bonus_tiles: list[Tile]
    winning_tile: Tile
    self_drawn: bool
    seat_wind: Wind
    prevailing_wind: Wind
    is_last_tile: bool = False  # last tile from wall
    is_kong_replacement: bool = False  # won off a kong replacement draw
    is_robbing_kong: bool = False  # won by robbing someone's kong


@dataclass
class FaanItem:
    """A single scoring pattern match."""

    name: str
    faan: int


@dataclass
class ScoreResult:
    """Complete scoring result."""

    items: list[FaanItem]
    total_faan: int
    is_limit: bool

    @property
    def valid(self) -> bool:
        """HK mahjong requires minimum 3 faan to win."""
        return self.total_faan >= 3


def score_hand(ctx: ScoringContext) -> ScoreResult:
    """Calculate the faan for a winning hand."""
    items: list[FaanItem] = []

    all_melds = list(ctx.decomposition.melds)
    pair_tile = ctx.decomposition.pair

    # Check for special hands first
    if _check_thirteen_orphans(ctx):
        return ScoreResult(
            items=[FaanItem("Thirteen Orphans", LIMIT_FAAN)],
            total_faan=LIMIT_FAAN,
            is_limit=True,
        )

    all_tiles = list(ctx.concealed_tiles)
    for m in ctx.exposed_melds:
        all_tiles.extend(m.tiles)

    # Limit hands
    limit = _check_limit_hands(ctx, all_melds, pair_tile, all_tiles)
    if limit is not None:
        return limit

    # Regular patterns
    items.extend(_check_dragon_pongs(all_melds))
    items.extend(_check_wind_pongs(all_melds, ctx.seat_wind, ctx.prevailing_wind))
    items.extend(_check_suit_patterns(all_melds, pair_tile, all_tiles))
    items.extend(_check_pong_patterns(all_melds))
    items.extend(_check_draw_patterns(ctx))
    items.extend(_check_bonus_tiles(ctx))

    # All concealed (no exposed melds except concealed kongs)
    if all(m.is_concealed for m in ctx.exposed_melds) and len(ctx.exposed_melds) == 0:
        items.append(FaanItem("Fully Concealed", 1))

    # No flowers
    if not ctx.bonus_tiles:
        items.append(FaanItem("No Flowers", 1))

    total = sum(item.faan for item in items)
    is_limit = total >= LIMIT_FAAN
    if is_limit:
        total = LIMIT_FAAN

    return ScoreResult(items=items, total_faan=total, is_limit=is_limit)


def _check_thirteen_orphans(ctx: ScoringContext) -> bool:
    return len(ctx.decomposition.melds) == 0 and ctx.decomposition.pair is not None


def _check_limit_hands(
    ctx: ScoringContext,
    all_melds: list[Meld],
    pair_tile: Tile,
    all_tiles: list[Tile],
) -> ScoreResult | None:
    # All Honors
    if all(t.is_honor for t in all_tiles) and pair_tile.is_honor:
        return ScoreResult(
            items=[FaanItem("All Honors", LIMIT_FAAN)],
            total_faan=LIMIT_FAAN,
            is_limit=True,
        )

    # Great Winds (大四喜) - pong/kong of all 4 winds
    wind_melds = [m for m in all_melds if m.first_tile.wind is not None and not m.is_chow]
    wind_types = {m.first_tile.wind for m in wind_melds}
    if len(wind_types) == 4:
        return ScoreResult(
            items=[FaanItem("Great Winds", LIMIT_FAAN)],
            total_faan=LIMIT_FAAN,
            is_limit=True,
        )

    # Great Dragons (大三元) - pong/kong of all 3 dragons
    dragon_melds = [m for m in all_melds if m.first_tile.dragon is not None and not m.is_chow]
    dragon_types = {m.first_tile.dragon for m in dragon_melds}
    if len(dragon_types) == 3:
        return ScoreResult(
            items=[FaanItem("Great Dragons", LIMIT_FAAN)],
            total_faan=LIMIT_FAAN,
            is_limit=True,
        )

    # All Terminals
    if all(t.is_terminal for t in all_tiles) and pair_tile.is_terminal:
        return ScoreResult(
            items=[FaanItem("All Terminals", LIMIT_FAAN)],
            total_faan=LIMIT_FAAN,
            is_limit=True,
        )

    # All Kongs
    if len(all_melds) == 4 and all(m.is_kong for m in all_melds):
        return ScoreResult(
            items=[FaanItem("All Kongs", LIMIT_FAAN)],
            total_faan=LIMIT_FAAN,
            is_limit=True,
        )

    # Nine Gates (九蓮寶燈) - concealed 1112345678999 + any of same suit
    if not ctx.exposed_melds:
        suited = [t for t in all_tiles if t.is_suited]
        if len(suited) == 14:
            suits = {t.suit for t in suited}
            if len(suits) == 1:
                from collections import Counter
                ranks = Counter(t.rank for t in suited)
                base = {1: 3, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 3}
                extra = Counter(ranks)
                for r, c in base.items():
                    extra[r] -= c
                remaining = {r: c for r, c in extra.items() if c > 0}
                if sum(remaining.values()) == 1:
                    return ScoreResult(
                        items=[FaanItem("Nine Gates", LIMIT_FAAN)],
                        total_faan=LIMIT_FAAN,
                        is_limit=True,
                    )

    return None


def _check_dragon_pongs(all_melds: list[Meld]) -> list[FaanItem]:
    items: list[FaanItem] = []
    for meld in all_melds:
        if meld.first_tile.dragon is not None and (meld.is_pong or meld.is_kong):
            name = {
                Dragon.RED: "Red Dragon Pong",
                Dragon.GREEN: "Green Dragon Pong",
                Dragon.WHITE: "White Dragon Pong",
            }[meld.first_tile.dragon]
            items.append(FaanItem(name, 1))
    return items


def _check_wind_pongs(
    all_melds: list[Meld], seat_wind: Wind, prevailing_wind: Wind
) -> list[FaanItem]:
    items: list[FaanItem] = []
    for meld in all_melds:
        if meld.first_tile.wind is not None and (meld.is_pong or meld.is_kong):
            wind = meld.first_tile.wind
            if wind == seat_wind:
                items.append(FaanItem("Seat Wind", 1))
            if wind == prevailing_wind:
                items.append(FaanItem("Prevailing Wind", 1))
    return items


def _check_suit_patterns(
    all_melds: list[Meld], pair_tile: Tile, all_tiles: list[Tile]
) -> list[FaanItem]:
    items: list[FaanItem] = []
    suited = [t for t in all_tiles if t.is_suited]
    honors = [t for t in all_tiles if t.is_honor]

    if not suited:
        return items

    suits_used = {t.suit for t in suited}

    if len(suits_used) == 1:
        if not honors and (not pair_tile.is_honor):
            # Pure one suit (清一色) - 7 faan
            items.append(FaanItem("Pure One Suit", 7))
        elif honors:
            # Mixed one suit (混一色) - 3 faan
            items.append(FaanItem("Mixed One Suit", 3))

    # All terminals and honors (混老頭)
    if all(t.is_terminal_or_honor for t in all_tiles):
        items.append(FaanItem("All Terminals and Honors", 1))

    return items


def _check_pong_patterns(all_melds: list[Meld]) -> list[FaanItem]:
    items: list[FaanItem] = []
    if all_melds and all(m.is_pong or m.is_kong for m in all_melds):
        items.append(FaanItem("All Pongs", 3))
    return items


def _check_draw_patterns(ctx: ScoringContext) -> list[FaanItem]:
    items: list[FaanItem] = []
    if ctx.self_drawn:
        items.append(FaanItem("Self Drawn", 1))
    if ctx.is_last_tile:
        items.append(FaanItem("Win on Last Tile", 1))
    if ctx.is_kong_replacement:
        items.append(FaanItem("Win on Kong Replacement", 1))
    if ctx.is_robbing_kong:
        items.append(FaanItem("Robbing the Kong", 1))
    return items


def _check_bonus_tiles(ctx: ScoringContext) -> list[FaanItem]:
    items: list[FaanItem] = []
    seat_num = {Wind.EAST: 1, Wind.SOUTH: 2, Wind.WEST: 3, Wind.NORTH: 4}[ctx.seat_wind]
    for tile in ctx.bonus_tiles:
        assert tile.bonus_type is not None
        if tile.bonus_number == seat_num:
            name = "Flower" if tile.bonus_type == BonusType.FLOWER else "Season"
            items.append(FaanItem(f"Matching {name}", 1))

    # All flowers or all seasons
    flowers = [t for t in ctx.bonus_tiles if t.bonus_type == BonusType.FLOWER]
    seasons = [t for t in ctx.bonus_tiles if t.bonus_type == BonusType.SEASON]
    if len(flowers) == 4:
        items.append(FaanItem("All Flowers", 2))
    if len(seasons) == 4:
        items.append(FaanItem("All Seasons", 2))

    # Small dragons (小三元) - 2 dragon pongs + dragon pair
    return items


def _check_small_dragons(
    all_melds: list[Meld], pair_tile: Tile
) -> list[FaanItem]:
    """Check for Small Dragons (小三元) - 2 dragon pong/kongs + dragon pair."""
    dragon_melds = [
        m for m in all_melds
        if m.first_tile.dragon is not None and (m.is_pong or m.is_kong)
    ]
    if len(dragon_melds) == 2 and pair_tile.dragon is not None:
        return [FaanItem("Small Dragons", 5)]
    return []


def _check_small_winds(
    all_melds: list[Meld], pair_tile: Tile
) -> list[FaanItem]:
    """Check for Small Winds (小四喜) - 3 wind pong/kongs + wind pair."""
    wind_melds = [
        m for m in all_melds
        if m.first_tile.wind is not None and (m.is_pong or m.is_kong)
    ]
    if len(wind_melds) == 3 and pair_tile.wind is not None:
        return [FaanItem("Small Winds", 6)]
    return []
