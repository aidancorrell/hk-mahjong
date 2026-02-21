"""Basic greedy AI strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hk_mahjong.ai.evaluator import calculate_shanten, tile_danger_score, tile_utility
from hk_mahjong.ai.strategy import Strategy
from hk_mahjong.core.game_state import ActionType
from hk_mahjong.core.rules import Claim, ClaimType
from hk_mahjong.core.tiles import Tile
from hk_mahjong.core.win_check import check_win

if TYPE_CHECKING:
    from hk_mahjong.core.game_state import GameState
    from hk_mahjong.core.player import Player


class BasicAI(Strategy):
    """Greedy meld-completion AI.

    Discard: minimize shanten, break isolated tiles.
    Claims: pong if improves shanten, chow only when close to winning.
    Always claim valid win.
    """

    def choose_discard(self, player: Player, game: GameState) -> Tile:
        hand = player.hand
        tiles = list(hand.concealed)

        if not tiles:
            raise ValueError("No tiles to discard")

        all_discards = [p.discards for p in game.players]
        current_shanten = calculate_shanten(tiles, hand.melds)

        best_tile = tiles[0]
        best_score = float("-inf")

        for tile in set(tiles):
            # Try discarding this tile
            remaining = list(tiles)
            remaining.remove(tile)
            new_shanten = calculate_shanten(remaining, hand.melds)

            # Score: prefer tiles that lower shanten
            score = (current_shanten - new_shanten) * 10.0
            # Safety bonus
            score -= tile_danger_score(tile, all_discards) * 0.5
            # Utility penalty (prefer discarding low-utility tiles)
            score -= tile_utility(tile, tiles) * 0.3

            if score > best_score:
                best_score = score
                best_tile = tile

        return best_tile

    def choose_claim(
        self, player: Player, tile: Tile, valid_claims: list[ClaimType], game: GameState
    ) -> Claim:
        # Always claim win
        if ClaimType.WIN in valid_claims:
            return Claim(player.seat, ClaimType.WIN)

        hand = player.hand
        current_shanten = calculate_shanten(hand.concealed, hand.melds)

        # Pong if it improves shanten significantly
        if ClaimType.PONG in valid_claims and current_shanten > 0:
            test_tiles = list(hand.concealed)
            # Simulate pong: remove 2 tiles, check shanten
            if hand.can_pong(tile):
                test = list(test_tiles)
                test.remove(tile)  # remove one copy
                test.remove(tile)  # remove second copy
                # After pong, we need to discard, so estimate improvement
                from hk_mahjong.core.meld import make_pong
                new_melds = list(hand.melds) + [make_pong(tile)]
                if test:
                    new_shanten = calculate_shanten(test, new_melds)
                    if new_shanten < current_shanten:
                        return Claim(player.seat, ClaimType.PONG)

        # Kong if available and shanten is okay
        if ClaimType.KONG in valid_claims:
            return Claim(player.seat, ClaimType.KONG)

        # Chow only if close to winning (shanten <= 2)
        if ClaimType.CHOW in valid_claims and current_shanten <= 2:
            chow_options = hand.can_chow(tile)
            if chow_options:
                companions = chow_options[0]
                return Claim(
                    player.seat, ClaimType.CHOW,
                    companions=companions,
                )

        return Claim(player.seat, ClaimType.PASS)

    def choose_action_after_draw(
        self, player: Player, game: GameState
    ) -> ActionType:
        # Check for win first
        if check_win(player.hand.concealed, player.hand.melds):
            return ActionType.DECLARE_WIN

        # Check for kong opportunities
        kong_tiles = player.hand.can_self_kong()
        if kong_tiles:
            # Only declare kong if we have spare tiles and it won't hurt
            return ActionType.DECLARE_CONCEALED_KONG

        return ActionType.DISCARD
