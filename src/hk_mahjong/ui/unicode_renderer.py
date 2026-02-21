"""Unicode mahjong tile renderer — emoji glyph + text label on two lines.

Tiles render as:
  🀇  🀈  🀉  🀀  🀄
  1B  2B  3B  EW  RD

The emoji gives the visual "tile image", the label makes it readable.
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

_WIND_MAP = {
    Wind.EAST: "\U0001F000",
    Wind.SOUTH: "\U0001F001",
    Wind.WEST: "\U0001F002",
    Wind.NORTH: "\U0001F003",
}
_DRAGON_MAP = {
    Dragon.RED: "\U0001F004",
    Dragon.GREEN: "\U0001F005",
    Dragon.WHITE: "\U0001F006",
}
_SUIT_BASE = {
    Suit.CHARACTERS: 0x1F007,
    Suit.BAMBOO: 0x1F010,
    Suit.DOTS: 0x1F019,
}
_BONUS_BASE = {
    BonusType.FLOWER: 0x1F022,
    BonusType.SEASON: 0x1F026,
}

_SUIT_COLORS = {
    Suit.BAMBOO: colors.BAMBOO,
    Suit.CHARACTERS: colors.CHARACTERS,
    Suit.DOTS: colors.DOTS,
}
_SUIT_LETTER = {Suit.BAMBOO: "B", Suit.CHARACTERS: "C", Suit.DOTS: "D"}
_WIND_CODE = {
    Wind.EAST: "E", Wind.SOUTH: "S", Wind.WEST: "W", Wind.NORTH: "N",
}
_DRAGON_CODE = {Dragon.RED: "R", Dragon.GREEN: "G", Dragon.WHITE: "W"}
_BONUS_CODE = {BonusType.FLOWER: "F", BonusType.SEASON: "S"}


def _char(tile: Tile) -> str:
    if tile.suit is not None:
        return chr(_SUIT_BASE[tile.suit] + (tile.rank - 1))
    if tile.wind is not None:
        return _WIND_MAP[tile.wind]
    if tile.dragon is not None:
        return _DRAGON_MAP[tile.dragon]
    assert tile.bonus_type is not None
    return chr(_BONUS_BASE[tile.bonus_type] + (tile.bonus_number - 1))


def _code(tile: Tile) -> str:
    """Short 2-3 char text code."""
    if tile.suit is not None:
        return f"{tile.rank}{_SUIT_LETTER[tile.suit]}"
    if tile.wind is not None:
        return f"{_WIND_CODE[tile.wind]}W"
    if tile.dragon is not None:
        return f"{_DRAGON_CODE[tile.dragon]}D"
    assert tile.bonus_type is not None
    return f"{_BONUS_CODE[tile.bonus_type]}{tile.bonus_number}"


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


# Each tile occupies 4 columns:  "XXYY" where XX = emoji (2-wide), YY = spaces
# We use 5 columns to give breathing room:  " X  " (space, emoji, 2 spaces)
_CELL = 5  # columns per tile


class UnicodeRenderer(TileRenderer):
    """Two-line renderer: emoji on top, text label below."""

    def render_tile(self, tile: Tile, selected: bool = False) -> str:
        ch = _char(tile)
        col = _color(tile)
        cd = _code(tile)
        if selected:
            return f"[bold reverse]{ch} {cd}[/bold reverse]"
        return f"[{col}]{ch} {cd}[/{col}]"

    def render_tile_back(self) -> str:
        return f"[{colors.TILE_BACK}]🀫[/{colors.TILE_BACK}]"

    def render_tile_row(
        self,
        tiles: Sequence[Tile],
        selected: int = -1,
        highlight: int = -1,
    ) -> list[Text]:
        """Two lines: emoji row + label row."""
        if not tiles:
            return [Text(""), Text("")]

        emoji_line = Text()
        label_line = Text()

        for i, tile in enumerate(tiles):
            ch = _char(tile)
            cd = _code(tile)
            col = _color(tile)

            if i == selected:
                # Highlighted selection: reverse video
                emoji_line.append(f" {ch}  ", style="bold reverse")
                label_line.append(f" {cd:<3}", style="bold reverse")
            elif i == highlight:
                emoji_line.append(f"▸{ch}◂ ", style="bold yellow")
                label_line.append(f"▸{cd:<2}◂", style="bold yellow")
            else:
                emoji_line.append(f" {ch}  ", style=col)
                label_line.append(f" {cd:<3}", style=col)

        return [emoji_line, label_line]

    def render_tile_row_compact(
        self,
        tiles: Sequence[Tile],
        highlight: int = -1,
    ) -> Text:
        """Single line: emoji followed by code."""
        line = Text()
        for i, tile in enumerate(tiles):
            ch = _char(tile)
            col = _color(tile)
            if i == highlight:
                line.append(ch, style="bold yellow underline")
            else:
                line.append(ch, style=col)
            line.append(" ")
        return line

    def tile_display_width(self) -> int:
        return _CELL
