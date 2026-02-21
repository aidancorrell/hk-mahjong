"""ASCII tile renderer — uses bordered text boxes.

┌──┐┌──┐┌──┐
│3B││4B││5B│
└──┘└──┘└──┘
"""

from __future__ import annotations

from collections.abc import Sequence

from rich.text import Text

from hk_mahjong.core.tiles import (
    BonusType,
    Dragon,
    Suit,
    Tile,
    Wind,
)
from hk_mahjong.ui import colors
from hk_mahjong.ui.renderer import TileRenderer

_SUIT_SHORT = {Suit.BAMBOO: "B", Suit.CHARACTERS: "C", Suit.DOTS: "D"}
_WIND_SHORT = {Wind.EAST: "E", Wind.SOUTH: "S", Wind.WEST: "W", Wind.NORTH: "N"}
_DRAGON_SHORT = {Dragon.RED: "R", Dragon.GREEN: "G", Dragon.WHITE: "W"}
_BONUS_SHORT = {BonusType.FLOWER: "F", BonusType.SEASON: "S"}

_SUIT_COLORS = {
    Suit.BAMBOO: colors.BAMBOO,
    Suit.CHARACTERS: colors.CHARACTERS,
    Suit.DOTS: colors.DOTS,
}


def _label(tile: Tile) -> str:
    if tile.suit is not None:
        return f"{tile.rank}{_SUIT_SHORT[tile.suit]}"
    if tile.wind is not None:
        return f"{_WIND_SHORT[tile.wind]}W"
    if tile.dragon is not None:
        return f"{_DRAGON_SHORT[tile.dragon]}D"
    assert tile.bonus_type is not None
    return f"{_BONUS_SHORT[tile.bonus_type]}{tile.bonus_number}"


def _color(tile: Tile) -> str:
    if tile.suit is not None:
        return _SUIT_COLORS[tile.suit]
    if tile.wind is not None:
        return colors.WIND
    if tile.dragon is not None:
        return {
            Dragon.RED: colors.DRAGON_RED,
            Dragon.GREEN: colors.DRAGON_GREEN,
            Dragon.WHITE: colors.DRAGON_WHITE,
        }[tile.dragon]
    return colors.BONUS


class AsciiRenderer(TileRenderer):
    """Renders tiles as 3-line bordered text boxes."""

    def render_tile(self, tile: Tile, selected: bool = False) -> str:
        lab = _label(tile)
        col = _color(tile)
        if selected:
            return f"[{colors.SELECTED}]\\[{lab}][/{colors.SELECTED}]"
        return f"[{col}]\\[{lab}][/{col}]"

    def render_tile_back(self) -> str:
        return f"[{colors.TILE_BACK}]\\[##][/{colors.TILE_BACK}]"

    def render_tile_row(
        self,
        tiles: Sequence[Tile],
        selected: int = -1,
        highlight: int = -1,
    ) -> list[Text]:
        if not tiles:
            return [Text(""), Text(""), Text("")]

        top = Text()
        mid = Text()
        bot = Text()

        for i, tile in enumerate(tiles):
            lab = _label(tile)
            col = _color(tile)

            if i == selected:
                top.append("┏━━┓", style="bold white")
                mid.append("┃", style="bold white")
                mid.append(lab, style=f"bold {col} reverse")
                mid.append("┃", style="bold white")
                bot.append("┗━━┛", style="bold white")
            elif i == highlight:
                top.append("╔══╗", style="bold yellow")
                mid.append("║", style="bold yellow")
                mid.append(lab, style=f"bold {col}")
                mid.append("║", style="bold yellow")
                bot.append("╚══╝", style="bold yellow")
            else:
                top.append("┌──┐", style="dim")
                mid.append("│", style="dim")
                mid.append(lab, style=col)
                mid.append("│", style="dim")
                bot.append("└──┘", style="dim")

        return [top, mid, bot]

    def render_tile_row_compact(
        self,
        tiles: Sequence[Tile],
        highlight: int = -1,
    ) -> Text:
        line = Text()
        for i, tile in enumerate(tiles):
            lab = _label(tile)
            col = _color(tile)
            if i == highlight:
                line.append(f"[{lab}]", style="bold yellow")
            else:
                line.append(f"[{lab}]", style=col)
            line.append(" ")
        return line

    def tile_display_width(self) -> int:
        return 4  # ┌──┐
