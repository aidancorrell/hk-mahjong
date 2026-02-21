"""Player state management."""

from __future__ import annotations

from dataclasses import dataclass, field

from hk_mahjong.core.hand import Hand
from hk_mahjong.core.tiles import Tile, Wind


@dataclass
class Player:
    """A mahjong player (human or AI)."""

    seat: int  # 0-3
    seat_wind: Wind
    hand: Hand = field(default_factory=Hand)
    score: int = 0
    is_human: bool = False
    name: str = ""
    discards: list[Tile] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            if self.is_human:
                self.name = "You"
            else:
                wind_names = {
                    Wind.EAST: "East",
                    Wind.SOUTH: "South",
                    Wind.WEST: "West",
                    Wind.NORTH: "North",
                }
                self.name = f"AI ({wind_names[self.seat_wind]})"

    def reset_hand(self) -> None:
        self.hand = Hand()
        self.discards = []
