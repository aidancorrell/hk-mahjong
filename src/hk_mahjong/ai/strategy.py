"""Base strategy interface for AI players."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from hk_mahjong.core.rules import Claim, ClaimType
from hk_mahjong.core.tiles import Tile

if TYPE_CHECKING:
    from hk_mahjong.core.game_state import ActionType, GameState
    from hk_mahjong.core.player import Player


class Strategy(ABC):
    """Abstract base for AI decision-making."""

    @abstractmethod
    def choose_discard(self, player: Player, game: GameState) -> Tile:
        """Choose which tile to discard from the player's hand."""
        ...

    @abstractmethod
    def choose_claim(
        self, player: Player, tile: Tile, valid_claims: list[ClaimType], game: GameState
    ) -> Claim:
        """Choose whether/how to claim a discarded tile."""
        ...

    @abstractmethod
    def choose_action_after_draw(
        self, player: Player, game: GameState
    ) -> ActionType:
        """After drawing, choose: discard, declare kong, or declare win."""
        ...
