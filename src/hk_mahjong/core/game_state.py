"""Game state machine for HK mahjong turn flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Protocol

from hk_mahjong.core.player import Player
from hk_mahjong.core.rules import (
    Claim,
    ClaimType,
    can_claim_chow,
)
from hk_mahjong.core.scoring import ScoreResult, ScoringContext, score_hand
from hk_mahjong.core.tiles import WIND_ORDER, Tile, Wind, sort_tiles
from hk_mahjong.core.wall import Wall, WallExhaustedError
from hk_mahjong.core.win_check import check_win


class TurnPhase(Enum):
    DEALING = auto()
    DRAWING = auto()          # current player draws from wall
    DRAWN = auto()            # player has drawn, must discard (or declare win/kong)
    DISCARDING = auto()       # player selects discard
    CLAIMING = auto()         # other players may claim the discard
    CLAIMING_RESOLVED = auto()  # claim resolved, executing
    ROUND_OVER = auto()       # someone won or wall exhausted
    GAME_OVER = auto()


class ActionType(Enum):
    DISCARD = auto()
    DRAW = auto()
    CLAIM_CHOW = auto()
    CLAIM_PONG = auto()
    CLAIM_KONG = auto()
    CLAIM_WIN = auto()
    DECLARE_CONCEALED_KONG = auto()
    DECLARE_PROMOTE_KONG = auto()
    DECLARE_WIN = auto()  # self-drawn win
    PASS = auto()


@dataclass
class Action:
    player_seat: int
    action_type: ActionType
    tile: Tile | None = None
    companions: tuple[Tile, ...] = ()


@dataclass
class RoundResult:
    winner: int | None  # seat index, None if draw
    score_result: ScoreResult | None = None
    winning_tile: Tile | None = None
    self_drawn: bool = False


class PlayerController(Protocol):
    """Interface for human/AI player decision making."""

    def choose_discard(self, player: Player, game: GameState) -> Tile: ...
    def choose_claim(
        self, player: Player, tile: Tile, game: GameState
    ) -> Claim: ...
    def choose_kong_or_win(self, player: Player, game: GameState) -> ActionType: ...


@dataclass
class GameState:
    """Full state of a mahjong game/round."""

    players: list[Player] = field(default_factory=list)
    wall: Wall = field(default_factory=Wall)
    current_player: int = 0  # seat index
    turn_phase: TurnPhase = TurnPhase.DEALING
    prevailing_wind: Wind = Wind.EAST
    dealer: int = 0
    last_discard: Tile | None = None
    last_discarder: int = -1
    round_result: RoundResult | None = None
    turn_count: int = 0
    kong_replacement: bool = False  # next draw is a kong replacement

    # Track for scoring
    _last_draw_was_replacement: bool = field(default=False, repr=False)

    def setup_round(
        self,
        prevailing_wind: Wind = Wind.EAST,
        dealer: int = 0,
        seed: int | None = None,
    ) -> None:
        """Set up a new round: create players, build wall, deal."""
        self.prevailing_wind = prevailing_wind
        self.dealer = dealer
        self.current_player = dealer
        self.turn_count = 0
        self.round_result = None
        self.last_discard = None
        self.last_discarder = -1

        winds = WIND_ORDER[dealer:] + WIND_ORDER[:dealer]

        if not self.players:
            self.players = [
                Player(seat=i, seat_wind=winds[i], is_human=(i == 0))
                for i in range(4)
            ]
        else:
            for i, p in enumerate(self.players):
                p.seat_wind = winds[i]
                p.reset_hand()

        self.wall = Wall(seed=seed)
        hands = self.wall.deal()

        for i, tiles in enumerate(hands):
            self.players[i].hand.concealed = list(tiles)
            # Separate bonus tiles
            self._replace_bonus_tiles(i)

        # Sort hands
        for p in self.players:
            p.hand.concealed = sort_tiles(p.hand.concealed)

        self.turn_phase = TurnPhase.DRAWING

    def _replace_bonus_tiles(self, seat: int) -> None:
        """Move bonus tiles to bonus area and draw replacements."""
        hand = self.players[seat].hand
        while True:
            bonus = [t for t in hand.concealed if t.is_bonus]
            if not bonus:
                break
            for b in bonus:
                hand.concealed.remove(b)
                hand.add_bonus(b)
                try:
                    replacement = self.wall.draw_replacement()
                    hand.concealed.append(replacement)
                except WallExhaustedError:
                    break

    def do_draw(self) -> Tile:
        """Current player draws from the wall."""
        if self.kong_replacement:
            tile = self.wall.draw_replacement()
            self.kong_replacement = False
            self._last_draw_was_replacement = True
        else:
            tile = self.wall.draw()
            self._last_draw_was_replacement = False

        player = self.players[self.current_player]
        player.hand.add(tile)

        # Handle bonus tile draws
        if tile.is_bonus:
            player.hand.concealed.remove(tile)
            player.hand.add_bonus(tile)
            try:
                replacement = self.wall.draw_replacement()
                player.hand.add(replacement)
                if replacement.is_bonus:
                    self._replace_bonus_tiles(self.current_player)
                tile = replacement
            except WallExhaustedError:
                self.turn_phase = TurnPhase.ROUND_OVER
                self.round_result = RoundResult(winner=None)
                return tile

        self.turn_phase = TurnPhase.DRAWN
        self.turn_count += 1
        return tile

    def do_discard(self, tile: Tile) -> None:
        """Current player discards a tile."""
        player = self.players[self.current_player]
        player.hand.remove(tile)
        player.discards.append(tile)
        self.last_discard = tile
        self.last_discarder = self.current_player
        self.turn_phase = TurnPhase.CLAIMING

    def do_self_drawn_win(self) -> RoundResult:
        """Current player declares a self-drawn win."""
        player = self.players[self.current_player]
        decomps = check_win(player.hand.concealed, player.hand.melds)
        if not decomps:
            raise ValueError("Not a winning hand")

        # Pick the highest-scoring decomposition
        best_result: ScoreResult | None = None
        winning_tile = player.hand.concealed[-1]  # last drawn tile

        for decomp in decomps:
            ctx = ScoringContext(
                decomposition=decomp,
                exposed_melds=player.hand.melds,
                concealed_tiles=player.hand.concealed,
                bonus_tiles=player.hand.bonus,
                winning_tile=winning_tile,
                self_drawn=True,
                seat_wind=player.seat_wind,
                prevailing_wind=self.prevailing_wind,
                is_kong_replacement=self._last_draw_was_replacement,
                is_last_tile=self.wall.is_exhausted,
            )
            result = score_hand(ctx)
            if best_result is None or result.total_faan > best_result.total_faan:
                best_result = result

        assert best_result is not None
        self.round_result = RoundResult(
            winner=self.current_player,
            score_result=best_result,
            winning_tile=winning_tile,
            self_drawn=True,
        )
        self.turn_phase = TurnPhase.ROUND_OVER
        return self.round_result

    def do_declare_kong(self, tile: Tile, concealed: bool = False, promote: bool = False) -> None:
        """Current player declares a kong from their hand."""
        player = self.players[self.current_player]
        if concealed:
            player.hand.declare_concealed_kong(tile)
        elif promote:
            player.hand.promote_kong(tile)
        self.kong_replacement = True
        # After declaring kong, player draws a replacement
        self.turn_phase = TurnPhase.DRAWING

    def resolve_claim(self, claim: Claim) -> None:
        """Execute a resolved claim on the last discard."""
        assert self.last_discard is not None
        tile = self.last_discard
        player = self.players[claim.player_seat]

        if claim.claim_type == ClaimType.WIN:
            # Add the claimed tile to concealed for win check
            player.hand.add(tile)
            decomps = check_win(player.hand.concealed, player.hand.melds)
            if not decomps:
                player.hand.remove(tile)
                raise ValueError("Not a winning hand")

            best_result: ScoreResult | None = None
            for decomp in decomps:
                ctx = ScoringContext(
                    decomposition=decomp,
                    exposed_melds=player.hand.melds,
                    concealed_tiles=player.hand.concealed,
                    bonus_tiles=player.hand.bonus,
                    winning_tile=tile,
                    self_drawn=False,
                    seat_wind=player.seat_wind,
                    prevailing_wind=self.prevailing_wind,
                )
                result = score_hand(ctx)
                if best_result is None or result.total_faan > best_result.total_faan:
                    best_result = result

            assert best_result is not None
            self.round_result = RoundResult(
                winner=claim.player_seat,
                score_result=best_result,
                winning_tile=tile,
                self_drawn=False,
            )
            self.turn_phase = TurnPhase.ROUND_OVER

        elif claim.claim_type == ClaimType.PONG:
            player.hand.declare_pong(tile)
            self.current_player = claim.player_seat
            self.turn_phase = TurnPhase.DRAWN  # player must discard

        elif claim.claim_type == ClaimType.KONG:
            player.hand.declare_kong(tile)
            self.current_player = claim.player_seat
            self.kong_replacement = True
            self.turn_phase = TurnPhase.DRAWING

        elif claim.claim_type == ClaimType.CHOW:
            player.hand.declare_chow(tile, claim.companions)
            self.current_player = claim.player_seat
            self.turn_phase = TurnPhase.DRAWN  # player must discard

    def advance_turn(self) -> None:
        """Move to the next player's turn (no claim was made)."""
        self.current_player = (self.current_player + 1) % 4
        if self.wall.is_exhausted:
            self.turn_phase = TurnPhase.ROUND_OVER
            self.round_result = RoundResult(winner=None)
        else:
            self.turn_phase = TurnPhase.DRAWING

    def get_valid_claims(self, tile: Tile, discarder: int) -> dict[int, list[ClaimType]]:
        """Get all valid claims each player can make on a discard."""
        claims: dict[int, list[ClaimType]] = {}
        for i, player in enumerate(self.players):
            if i == discarder:
                continue
            valid: list[ClaimType] = []
            # Win check
            test_concealed = list(player.hand.concealed) + [tile]
            if check_win(test_concealed, player.hand.melds):
                valid.append(ClaimType.WIN)
            # Kong
            if player.hand.can_kong(tile):
                valid.append(ClaimType.KONG)
            # Pong
            if player.hand.can_pong(tile):
                valid.append(ClaimType.PONG)
            # Chow (only from left player)
            if can_claim_chow(i, discarder) and player.hand.can_chow(tile):
                valid.append(ClaimType.CHOW)
            if valid:
                claims[i] = valid
        return claims

    def can_self_win(self) -> bool:
        """Check if current player can declare a self-drawn win."""
        player = self.players[self.current_player]
        return len(check_win(player.hand.concealed, player.hand.melds)) > 0
