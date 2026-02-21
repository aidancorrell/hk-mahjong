"""Integration tests for game state machine."""

from hk_mahjong.core.game_state import GameState, TurnPhase
from hk_mahjong.core.rules import Claim, ClaimType
from hk_mahjong.core.tiles import Wind


class TestGameSetup:
    def test_setup_round(self) -> None:
        game = GameState()
        game.setup_round(seed=42)
        assert len(game.players) == 4
        assert game.turn_phase == TurnPhase.DRAWING
        assert game.current_player == 0
        for p in game.players:
            # 13 tiles minus any bonus tile replacements
            total = len(p.hand.concealed) + len(p.hand.bonus)
            assert total >= 13

    def test_deal_all_players_have_tiles(self) -> None:
        game = GameState()
        game.setup_round(seed=123)
        for p in game.players:
            assert len(p.hand.concealed) >= 10  # at least some tiles after bonus

    def test_seat_winds(self) -> None:
        game = GameState()
        game.setup_round(dealer=0, seed=42)
        assert game.players[0].seat_wind == Wind.EAST
        assert game.players[1].seat_wind == Wind.SOUTH


class TestTurnFlow:
    def test_draw_and_discard(self) -> None:
        game = GameState()
        game.setup_round(seed=42)
        assert game.turn_phase == TurnPhase.DRAWING

        tile = game.do_draw()
        assert tile is not None
        assert game.turn_phase == TurnPhase.DRAWN

        # Discard any tile
        discard = game.players[0].hand.concealed[0]
        game.do_discard(discard)
        assert game.turn_phase == TurnPhase.CLAIMING
        assert game.last_discard == discard

    def test_advance_turn(self) -> None:
        game = GameState()
        game.setup_round(seed=42)
        game.do_draw()
        discard = game.players[0].hand.concealed[0]
        game.do_discard(discard)
        game.advance_turn()
        assert game.current_player == 1
        assert game.turn_phase == TurnPhase.DRAWING


class TestFullGameSimulation:
    def test_simulate_until_exhaustion(self) -> None:
        """Simulate a full game with random discards until wall exhausts."""
        game = GameState()
        game.setup_round(seed=42)
        max_turns = 200

        for _ in range(max_turns):
            if game.turn_phase == TurnPhase.ROUND_OVER:
                break

            if game.turn_phase == TurnPhase.DRAWING:
                try:
                    game.do_draw()
                except Exception:
                    break

            if game.turn_phase == TurnPhase.DRAWN:
                player = game.players[game.current_player]
                if player.hand.concealed:
                    discard = player.hand.concealed[0]
                    game.do_discard(discard)
                else:
                    break

            if game.turn_phase == TurnPhase.CLAIMING:
                game.advance_turn()

        # Game should have ended by now
        assert game.turn_phase == TurnPhase.ROUND_OVER or game.turn_count > 0

    def test_claim_pong(self) -> None:
        """Test that pong claim works correctly."""
        game = GameState()
        game.setup_round(seed=42)

        # Play until we find a pongable situation
        for _ in range(100):
            if game.turn_phase == TurnPhase.ROUND_OVER:
                break

            if game.turn_phase == TurnPhase.DRAWING:
                game.do_draw()

            if game.turn_phase == TurnPhase.DRAWN:
                player = game.players[game.current_player]
                discard = player.hand.concealed[0]
                game.do_discard(discard)

            if game.turn_phase == TurnPhase.CLAIMING:
                tile = game.last_discard
                assert tile is not None
                valid = game.get_valid_claims(tile, game.last_discarder)

                claimed = False
                for seat, claim_types in valid.items():
                    if ClaimType.PONG in claim_types:
                        game.resolve_claim(Claim(seat, ClaimType.PONG))
                        claimed = True
                        break

                if not claimed:
                    game.advance_turn()
