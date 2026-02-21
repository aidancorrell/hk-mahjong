"""Wall management for dealing and drawing tiles."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from hk_mahjong.core.tiles import create_full_tileset

if TYPE_CHECKING:
    from hk_mahjong.core.tiles import Tile


class WallExhaustedError(Exception):
    """Raised when the wall has no more drawable tiles."""


class Wall:
    """The wall of tiles for a mahjong game.

    After shuffling, the last 14 tiles are reserved as the dead wall
    (for kong replacement draws). The remaining tiles are the live wall.
    """

    DEAD_WALL_SIZE = 14

    def __init__(
        self,
        tiles: list[Tile] | None = None,
        seed: int | None = None,
    ) -> None:
        if tiles is not None:
            self._tiles = list(tiles)
        else:
            self._tiles = create_full_tileset()
        rng = random.Random(seed)
        rng.shuffle(self._tiles)
        # Split: live wall is everything except last DEAD_WALL_SIZE tiles
        self._dead_wall = self._tiles[-self.DEAD_WALL_SIZE :]
        self._live_wall = self._tiles[: -self.DEAD_WALL_SIZE]
        self._draw_index = 0
        self._dead_draw_index = 0

    @property
    def tiles_remaining(self) -> int:
        return len(self._live_wall) - self._draw_index

    @property
    def dead_wall_remaining(self) -> int:
        return len(self._dead_wall) - self._dead_draw_index

    @property
    def is_exhausted(self) -> bool:
        return self._draw_index >= len(self._live_wall)

    def draw(self) -> Tile:
        """Draw the next tile from the live wall."""
        if self.is_exhausted:
            raise WallExhaustedError("No tiles remaining in the live wall")
        tile = self._live_wall[self._draw_index]
        self._draw_index += 1
        return tile

    def draw_replacement(self) -> Tile:
        """Draw from the dead wall (for kong replacement)."""
        if self._dead_draw_index >= len(self._dead_wall):
            raise WallExhaustedError("No tiles remaining in the dead wall")
        tile = self._dead_wall[self._dead_draw_index]
        self._dead_draw_index += 1
        return tile

    def deal(self, num_players: int = 4) -> list[list[Tile]]:
        """Deal initial hands: 13 tiles each (dealer gets 14 in game logic, not here).

        Returns a list of 4 hands, each with 13 tiles.
        """
        hands: list[list[Tile]] = [[] for _ in range(num_players)]
        # Deal in groups of 4 tiles, 3 rounds, then 1 tile each
        for _ in range(3):
            for p in range(num_players):
                for _ in range(4):
                    hands[p].append(self.draw())
        for p in range(num_players):
            hands[p].append(self.draw())
        return hands
