"""Abstract renderer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from rich.text import Text

from hk_mahjong.core.tiles import Tile


class TileRenderer(ABC):
    """Renders tiles for the board."""

    @abstractmethod
    def render_tile(self, tile: Tile, selected: bool = False) -> str:
        """Render a single tile as a rich-markup string (inline)."""
        ...

    @abstractmethod
    def render_tile_back(self) -> str:
        """Render a face-down tile (inline)."""
        ...

    @abstractmethod
    def render_tile_row(
        self,
        tiles: Sequence[Tile],
        selected: int = -1,
        highlight: int = -1,
    ) -> list[Text]:
        """Render a row of tiles as one or more Text lines.

        selected: index of selected tile
        highlight: index of highlighted tile (e.g. last discard)
        Returns list of Text lines.
        """
        ...

    @abstractmethod
    def render_tile_row_compact(
        self,
        tiles: Sequence[Tile],
        highlight: int = -1,
    ) -> Text:
        """Render tiles in a single compact line (for discards etc)."""
        ...

    @abstractmethod
    def tile_display_width(self) -> int:
        """Approximate display width per tile (for index alignment)."""
        ...
