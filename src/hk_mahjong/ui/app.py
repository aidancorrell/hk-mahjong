"""Main game loop connecting GameState to terminal UI."""

from __future__ import annotations

import curses
import time
from typing import Any

from rich.console import Console

from hk_mahjong.ai.basic_ai import BasicAI
from hk_mahjong.core.game_state import ActionType, GameState, TurnPhase
from hk_mahjong.core.player import Player
from hk_mahjong.core.rules import Claim, ClaimType, resolve_claims
from hk_mahjong.core.tiles import Tile, sort_tiles
from hk_mahjong.ui.ascii_renderer import AsciiRenderer
from hk_mahjong.ui.board import BoardView
from hk_mahjong.ui.prompt import claim_prompt_text, parse_claim_key
from hk_mahjong.ui.renderer import TileRenderer
from hk_mahjong.ui.unicode_renderer import UnicodeRenderer

# How long to pause so the player can read AI actions
AI_DISCARD_PAUSE = 0.8
AI_CLAIM_PAUSE = 1.2
AI_KONG_PAUSE = 1.0
AI_WIN_PAUSE = 2.0


class App:
    """Main game application."""

    def __init__(
        self, use_unicode: bool = True, seed: int | None = None
    ) -> None:
        self.console = Console()
        if use_unicode:
            self.renderer: TileRenderer = UnicodeRenderer()
        else:
            self.renderer = AsciiRenderer()
        self.board = BoardView(self.renderer)
        self.game = GameState()
        self.ai = BasicAI()
        self.selected_index = 0
        self.message = ""
        self.seed = seed
        self._running = True

    def run(self) -> None:
        """Run the game using curses for input."""
        curses.wrapper(self._curses_main)

    def _curses_main(self, stdscr: Any) -> None:
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.timeout(100)

        self.game.setup_round(seed=self.seed)
        self._refresh_display()

        while self._running:
            phase = self.game.turn_phase

            if phase == TurnPhase.ROUND_OVER:
                self._handle_round_over(stdscr)
                break

            if self.game.current_player == 0:
                self._handle_human_turn(stdscr)
            else:
                self._handle_ai_turn(stdscr)

    def _refresh_display(self) -> None:
        self.console.clear()
        self.board.render(
            self.console, self.game, self.selected_index, self.message
        )

    def _handle_human_turn(self, stdscr: Any) -> None:
        phase = self.game.turn_phase

        if phase == TurnPhase.DRAWING:
            tile = self.game.do_draw()
            self.message = (
                "You drew a tile! (now in your hand, sorted)"
            )
            self._clamp_selection()
            self._refresh_display()

        elif phase == TurnPhase.DRAWN:
            # Check for win
            if self.game.can_self_win():
                self.message = "[w] Declare Win!   [any] Discard instead"
                self._refresh_display()
                key = self._wait_key(stdscr)
                if key == ord("w"):
                    self.game.do_self_drawn_win()
                    self._refresh_display()
                    return

            # Check for kong
            kong_tiles = self.game.players[0].hand.can_self_kong()
            if kong_tiles:
                name = kong_tiles[0].short_name()
                self.message = (
                    f"[k] Declare Kong ({name})   [any] Discard"
                )
                self._refresh_display()
                key = self._wait_key(stdscr)
                if key == ord("k"):
                    tile = kong_tiles[0]
                    count = self.game.players[0].hand.concealed.count(tile)
                    if count >= 4:
                        self.game.do_declare_kong(tile, concealed=True)
                    else:
                        self.game.do_declare_kong(tile, promote=True)
                    return

            self._discard_selection_loop(stdscr)

        elif phase == TurnPhase.CLAIMING:
            self.game.advance_turn()

    def _discard_selection_loop(self, stdscr: Any) -> None:
        player = self.game.players[0]
        sorted_tiles = sort_tiles(player.hand.concealed)
        self._clamp_selection()
        self.message = "Select tile to discard  (←/→ then Enter)"
        self._refresh_display()

        while True:
            key = self._wait_key(stdscr)
            if key == curses.KEY_LEFT:
                self.selected_index = max(0, self.selected_index - 1)
                self._refresh_display()
            elif key == curses.KEY_RIGHT:
                self.selected_index = min(
                    len(sorted_tiles) - 1, self.selected_index + 1
                )
                self._refresh_display()
            elif key in (curses.KEY_ENTER, 10, 13):
                tile = sorted_tiles[self.selected_index]
                self.game.do_discard(tile)
                self.message = f"You discarded {tile.short_name()}"
                self._refresh_display()
                time.sleep(0.4)
                self._process_claims_on_discard(stdscr)
                return
            elif key == ord("r"):
                self._toggle_renderer()
                self._refresh_display()
            elif key == ord("q"):
                self._running = False
                return

    def _process_claims_on_discard(self, stdscr: Any) -> None:
        """After human discards, let AI players claim."""
        assert self.game.last_discard is not None
        tile = self.game.last_discard
        discarder = self.game.last_discarder

        valid_claims = self.game.get_valid_claims(tile, discarder)
        if not valid_claims:
            self.game.advance_turn()
            return

        claims: list[Claim] = []
        for seat, claim_types in valid_claims.items():
            player = self.game.players[seat]
            if player.is_human:
                claim = self._prompt_human_claim(
                    stdscr, player, tile, claim_types
                )
                claims.append(claim)
            else:
                claim = self.ai.choose_claim(
                    player, tile, claim_types, self.game
                )
                claims.append(claim)

        winner = resolve_claims(claims)
        if winner is not None and winner.claim_type != ClaimType.PASS:
            pname = self.game.players[winner.player_seat].name
            ctype = winner.claim_type.name
            self.message = f"{pname} claims {ctype} on {tile.short_name()}!"
            self._refresh_display()
            time.sleep(AI_CLAIM_PAUSE)
            self.game.resolve_claim(winner)
        else:
            self.game.advance_turn()

    def _prompt_human_claim(
        self,
        stdscr: Any,
        player: Player,
        tile: Tile,
        valid_claims: list[ClaimType],
    ) -> Claim:
        prompt = claim_prompt_text(valid_claims)
        self.message = f"Claim {tile.short_name()}?  {prompt}"
        self._refresh_display()

        while True:
            key = self._wait_key(stdscr)
            ch = chr(key) if 0 < key < 128 else ""
            result = parse_claim_key(ch, valid_claims)
            if result is not None:
                if result == ClaimType.CHOW:
                    chow_options = player.hand.can_chow(tile)
                    if chow_options:
                        companions = chow_options[0]
                        return Claim(
                            player.seat,
                            ClaimType.CHOW,
                            companions=companions,
                        )
                return Claim(player.seat, result)

    def _handle_ai_turn(self, stdscr: Any) -> None:
        player = self.game.players[self.game.current_player]
        phase = self.game.turn_phase

        if phase == TurnPhase.DRAWING:
            try:
                self.game.do_draw()
            except Exception:
                return

        if self.game.turn_phase == TurnPhase.DRAWN:
            action = self.ai.choose_action_after_draw(player, self.game)

            if action == ActionType.DECLARE_WIN:
                try:
                    self.game.do_self_drawn_win()
                    self.message = (
                        f"{player.name} wins with a self-draw!"
                    )
                    self._refresh_display()
                    time.sleep(AI_WIN_PAUSE)
                    return
                except ValueError:
                    action = ActionType.DISCARD

            if action in (
                ActionType.DECLARE_CONCEALED_KONG,
                ActionType.DECLARE_PROMOTE_KONG,
            ):
                kong_tiles = player.hand.can_self_kong()
                if kong_tiles:
                    t = kong_tiles[0]
                    counts = player.hand.concealed.count(t)
                    if counts >= 4:
                        self.game.do_declare_kong(t, concealed=True)
                    else:
                        self.game.do_declare_kong(t, promote=True)
                    self.message = (
                        f"{player.name} declares Kong ({t.short_name()})!"
                    )
                    self._refresh_display()
                    time.sleep(AI_KONG_PAUSE)
                    return

            # Discard
            if self.game.turn_phase == TurnPhase.DRAWN:
                discard = self.ai.choose_discard(player, self.game)
                self.game.do_discard(discard)
                self.message = (
                    f"{player.name} discards {discard.short_name()}"
                )
                self._refresh_display()
                time.sleep(AI_DISCARD_PAUSE)
                self._process_claims_after_ai_discard(stdscr)

    def _process_claims_after_ai_discard(self, stdscr: Any) -> None:
        """After AI discards, check if human or other AI can claim."""
        assert self.game.last_discard is not None
        tile = self.game.last_discard
        discarder = self.game.last_discarder

        valid_claims = self.game.get_valid_claims(tile, discarder)
        if not valid_claims:
            self.game.advance_turn()
            return

        claims: list[Claim] = []
        for seat, claim_types in valid_claims.items():
            player = self.game.players[seat]
            if player.is_human:
                claim = self._prompt_human_claim(
                    stdscr, player, tile, claim_types
                )
                claims.append(claim)
            else:
                claim = self.ai.choose_claim(
                    player, tile, claim_types, self.game
                )
                claims.append(claim)

        winner = resolve_claims(claims)
        if winner is not None and winner.claim_type != ClaimType.PASS:
            pname = self.game.players[winner.player_seat].name
            ctype = winner.claim_type.name
            self.message = f"{pname} claims {ctype} on {tile.short_name()}!"
            self._refresh_display()
            time.sleep(AI_CLAIM_PAUSE)
            self.game.resolve_claim(winner)
        else:
            self.game.advance_turn()

    def _handle_round_over(self, stdscr: Any) -> None:
        result = self.game.round_result
        if result is None:
            self.message = "Round over — draw!"
        elif result.winner is not None:
            winner = self.game.players[result.winner]
            draw_type = "self-draw" if result.self_drawn else "discard"
            self.message = f"{winner.name} wins by {draw_type}!"
            if result.score_result:
                faan = result.score_result.total_faan
                self.message += f"  ({faan} faan)"
                if result.score_result.items:
                    patterns = ", ".join(
                        f.name for f in result.score_result.items
                    )
                    self.message += f"\n  Patterns: {patterns}"
        else:
            self.message = "Wall exhausted — draw!"

        self.message += "\n\n  Press any key to exit..."
        self._refresh_display()
        stdscr.timeout(-1)
        stdscr.getch()
        self._running = False

    def _toggle_renderer(self) -> None:
        if isinstance(self.renderer, UnicodeRenderer):
            self.renderer = AsciiRenderer()
        else:
            self.renderer = UnicodeRenderer()
        self.board = BoardView(self.renderer)

    def _clamp_selection(self) -> None:
        n = len(self.game.players[0].hand.concealed)
        if n == 0:
            self.selected_index = 0
        elif self.selected_index >= n:
            self.selected_index = n - 1

    def _wait_key(self, stdscr: Any) -> int:
        """Wait for a keypress, handling timeout."""
        while True:
            key = stdscr.getch()
            if key != -1:
                return key
