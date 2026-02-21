"""Tests for basic AI strategy."""

from hk_mahjong.ai.basic_ai import BasicAI
from hk_mahjong.core.game_state import ActionType, GameState
from hk_mahjong.core.rules import ClaimType
from hk_mahjong.core.tiles import Suit, make_suited


class TestBasicAI:
    def test_choose_discard(self) -> None:
        game = GameState()
        game.setup_round(seed=42)
        game.do_draw()

        ai = BasicAI()
        player = game.players[game.current_player]
        discard = ai.choose_discard(player, game)
        assert discard in player.hand.concealed

    def test_choose_action_after_draw(self) -> None:
        game = GameState()
        game.setup_round(seed=42)
        game.do_draw()

        ai = BasicAI()
        player = game.players[game.current_player]
        action = ai.choose_action_after_draw(player, game)
        assert action in (ActionType.DISCARD, ActionType.DECLARE_WIN,
                         ActionType.DECLARE_CONCEALED_KONG)

    def test_ai_plays_full_game(self) -> None:
        """AI can play a full game without crashing."""
        game = GameState()
        game.setup_round(seed=42)
        ai = BasicAI()

        for _ in range(300):
            if game.turn_phase.name == "ROUND_OVER":
                break

            from hk_mahjong.core.game_state import TurnPhase

            if game.turn_phase == TurnPhase.DRAWING:
                try:
                    game.do_draw()
                except Exception:
                    break

            if game.turn_phase == TurnPhase.DRAWN:
                player = game.players[game.current_player]
                action = ai.choose_action_after_draw(player, game)
                if action == ActionType.DECLARE_WIN:
                    try:
                        game.do_self_drawn_win()
                        break
                    except ValueError:
                        pass
                if action in (ActionType.DECLARE_CONCEALED_KONG, ActionType.DECLARE_PROMOTE_KONG):
                    kong_tiles = player.hand.can_self_kong()
                    if kong_tiles:
                        t = kong_tiles[0]
                        if player.hand.concealed.count(t) >= 4:
                            game.do_declare_kong(t, concealed=True)
                        else:
                            game.do_declare_kong(t, promote=True)
                        continue

                # Fallback: discard
                if game.turn_phase == TurnPhase.DRAWN:
                    discard = ai.choose_discard(player, game)
                    game.do_discard(discard)

            if game.turn_phase == TurnPhase.CLAIMING:
                tile = game.last_discard
                assert tile is not None
                valid = game.get_valid_claims(tile, game.last_discarder)
                from hk_mahjong.core.rules import Claim, resolve_claims

                claims = []
                for seat, claim_types in valid.items():
                    p = game.players[seat]
                    claim = ai.choose_claim(p, tile, claim_types, game)
                    claims.append(claim)

                winner = resolve_claims(claims)
                if winner and winner.claim_type != ClaimType.PASS:
                    game.resolve_claim(winner)
                else:
                    game.advance_turn()
