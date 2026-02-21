"""HK mahjong rules: claim priority, validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from hk_mahjong.core.tiles import Tile


class ClaimType(Enum):
    WIN = auto()
    KONG = auto()
    PONG = auto()
    CHOW = auto()
    PASS = auto()


# Priority order: WIN > KONG = PONG > CHOW > PASS
CLAIM_PRIORITY = {
    ClaimType.WIN: 4,
    ClaimType.KONG: 3,
    ClaimType.PONG: 3,
    ClaimType.CHOW: 2,
    ClaimType.PASS: 0,
}


@dataclass
class Claim:
    """A player's claim on a discarded tile."""

    player_seat: int
    claim_type: ClaimType
    companions: tuple[Tile, ...] = ()  # tiles from hand used in the claim


def resolve_claims(claims: list[Claim]) -> Claim | None:
    """Resolve competing claims on a discard.

    Priority: win > pong/kong > chow
    For equal priority, the player closest in turn order wins.
    Returns None if no claims or all passes.
    """
    non_pass = [c for c in claims if c.claim_type != ClaimType.PASS]
    if not non_pass:
        return None

    # Sort by priority (descending), then by seat (ascending for turn order)
    non_pass.sort(
        key=lambda c: (-CLAIM_PRIORITY[c.claim_type], c.player_seat)
    )
    return non_pass[0]


def can_claim_chow(claimant_seat: int, discarder_seat: int, num_players: int = 4) -> bool:
    """Chow can only be claimed by the player to the immediate right (next in turn)."""
    return (discarder_seat + 1) % num_players == claimant_seat
