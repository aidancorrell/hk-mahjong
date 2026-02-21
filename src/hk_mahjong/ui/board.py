"""Board layout — sequential panels, no Layout height allocation."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from hk_mahjong.core.game_state import GameState
from hk_mahjong.core.tiles import Suit, Tile, Wind, sort_tiles
from hk_mahjong.ui import colors
from hk_mahjong.ui.renderer import TileRenderer


def _tile_style(tile: Tile) -> str:
    """Get a color style string for a tile."""
    if tile.suit == Suit.BAMBOO:
        return colors.BAMBOO
    if tile.suit == Suit.CHARACTERS:
        return colors.CHARACTERS
    if tile.suit == Suit.DOTS:
        return colors.DOTS
    if tile.wind is not None:
        return colors.WIND
    if tile.dragon is not None:
        return "bold red" if tile.dragon.name == "RED" else (
            "bold green" if tile.dragon.name == "GREEN" else "bold white"
        )
    return colors.BONUS

_W = {
    Wind.EAST: "East", Wind.SOUTH: "South",
    Wind.WEST: "West", Wind.NORTH: "North",
}


class BoardView:
    def __init__(self, renderer: TileRenderer) -> None:
        self.renderer = renderer

    def render(
        self,
        console: Console,
        game: GameState,
        selected_index: int = 0,
        message: str = "",
    ) -> None:
        """Print all panels sequentially to the console."""
        console.print(self._header(game))
        console.print(self._opponents(game))
        console.print(self._table(game))
        console.print(self._hand(game, selected_index))
        console.print(self._action_bar(game, message))

    # ── header ─────────────────────────────────────────

    def _header(self, game: GameState) -> Panel:
        t = Text()
        t.append(" 🀄 HK MAHJONG ", style="bold white on dark_green")
        t.append("   ")
        t.append(f"Round: {_W[game.prevailing_wind]}", style=colors.HEADER)
        t.append("  │  ")
        t.append(f"You: {_W[game.players[0].seat_wind]}", style=colors.HEADER)
        t.append("  │  ")
        rem = game.wall.tiles_remaining
        filled = max(0, int(rem / 130 * 15))
        t.append("Wall ", style="dim")
        t.append("█" * filled, style="white")
        t.append("░" * (15 - filled), style="dim")
        t.append(f" {rem}", style="bold")
        t.append(f"  │  Turn {game.turn_count}", style="dim")
        return Panel(t, style="green")

    # ── opponents (all 3 in one horizontal row) ────────

    def _opponents(self, game: GameState) -> Panel:
        content = Text()
        for si, seat in enumerate(range(1, 4)):
            p = game.players[seat]
            active = seat == game.current_player
            wind = _W[p.seat_wind]
            arrow = " ◀" if active else ""
            sty = colors.PLAYER_ACTIVE if active else "bold"

            if si > 0:
                content.append("\n")

            content.append(f" {wind}{arrow} ", style=sty)
            content.append(f"({len(p.hand.concealed)})", style="dim")

            # show exposed melds inline
            if p.hand.melds:
                content.append("  Melds: ", style="dim")
                for meld in p.hand.melds:
                    content.append_text(
                        self.renderer.render_tile_row_compact(
                            list(meld.tiles)
                        )
                    )
                    content.append(" ")

            # bonus
            if p.hand.bonus:
                content.append(" Bonus: ", style="dim magenta")
                for bt in p.hand.bonus:
                    content.append_text(
                        Text.from_markup(
                            self.renderer.render_tile(bt)
                        )
                    )
                    content.append(" ")

        return Panel(
            content,
            title="Opponents",
            border_style="dim",
        )

    # ── table: discards ────────────────────────────────

    def _table(self, game: GameState) -> Panel:
        content = Text()

        for pi, p in enumerate(game.players):
            wind = _W[p.seat_wind]
            lbl = "You" if p.seat == 0 else wind
            is_discarder = p.seat == game.last_discarder

            if pi > 0:
                content.append("\n")

            content.append(f" {lbl:>5}: ", style="bold" if p.seat == 0 else "dim")

            if p.discards:
                last_i = len(p.discards) - 1
                for i, tile in enumerate(p.discards):
                    is_last = (
                        is_discarder
                        and i == last_i
                        and game.last_discard is not None
                    )
                    code = tile.short_name()
                    col = _tile_style(tile)
                    if is_last:
                        content.append(
                            f"[{code}]",
                            style="bold yellow underline",
                        )
                    else:
                        content.append(code, style=col)
                    content.append(" ")
            else:
                content.append("—", style="dim")

        # last discard callout
        if game.last_discard is not None:
            d = game.players[game.last_discarder]
            who = "You" if d.seat == 0 else d.name
            content.append("\n\n  ➤ Last: ", style="bold yellow")
            content.append(who, style="bold")
            content.append(" played ", style="dim")
            content.append_text(
                Text.from_markup(
                    self.renderer.render_tile(game.last_discard)
                )
            )

        return Panel(
            content,
            title="Table — Discards",
            border_style="blue",
        )

    # ── your hand ──────────────────────────────────────

    def _hand(self, game: GameState, selected: int) -> Panel:
        p = game.players[0]
        hand = p.hand
        tiles = sort_tiles(hand.concealed)
        parts: list[Text | str] = []

        # exposed melds inline
        if hand.melds:
            ml = Text("  Exposed: ", style="dim")
            for meld in hand.melds:
                ml.append_text(
                    self.renderer.render_tile_row_compact(
                        list(meld.tiles)
                    )
                )
                ml.append("  ")
            parts.append(ml)

        # concealed tiles
        if tiles:
            tile_lines = self.renderer.render_tile_row(
                tiles, selected=selected
            )
            for tl in tile_lines:
                padded = Text("  ")
                padded.append_text(tl)
                parts.append(padded)

            # index numbers
            idx = Text("  ")
            tw = self.renderer.tile_display_width()
            for i in range(len(tiles)):
                num = str(i + 1)
                pad_total = tw - len(num)
                lp = pad_total // 2
                rp = pad_total - lp
                sty = "bold white" if i == selected else "dim"
                idx.append(" " * lp + num + " " * rp, style=sty)
            parts.append(idx)

        # bonus
        if hand.bonus:
            bl = Text("  Bonus: ", style="dim magenta")
            for bt in hand.bonus:
                bl.append_text(
                    Text.from_markup(self.renderer.render_tile(bt))
                )
                bl.append(" ")
            parts.append(bl)

        active = game.current_player == 0
        wind = _W[p.seat_wind]
        marker = " ◀ YOUR TURN" if active else ""
        border = "bold green" if active else "green"
        return Panel(
            Group(*parts),
            title=f"Your Hand ({wind}){marker}",
            border_style=border,
        )

    # ── action bar ─────────────────────────────────────

    def _action_bar(self, game: GameState, message: str) -> Panel:
        t = Text()
        if message:
            t.append(message, style=colors.ACTION_BAR)
        else:
            t.append("  ←/→ ", style="bold")
            t.append("Select  ", style="dim")
            t.append("Enter ", style="bold")
            t.append("Discard  ", style="dim")
            t.append("r ", style="bold")
            t.append("Renderer  ", style="dim")
            t.append("q ", style="bold")
            t.append("Quit", style="dim")
        return Panel(t, border_style="yellow")
