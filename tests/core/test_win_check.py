"""Tests for win detection."""

from hk_mahjong.core.meld import Meld, MeldType, make_pong
from hk_mahjong.core.tiles import (
    Dragon,
    Suit,
    Wind,
    make_dragon,
    make_suited,
    make_wind,
)
from hk_mahjong.core.win_check import check_win, is_thirteen_orphans


class TestWinCheck:
    def test_simple_winning_hand(self) -> None:
        """4 melds + 1 pair, all concealed."""
        concealed = [
            # Chow: 1-2-3 bamboo
            make_suited(Suit.BAMBOO, 1),
            make_suited(Suit.BAMBOO, 2),
            make_suited(Suit.BAMBOO, 3),
            # Chow: 4-5-6 bamboo
            make_suited(Suit.BAMBOO, 4),
            make_suited(Suit.BAMBOO, 5),
            make_suited(Suit.BAMBOO, 6),
            # Chow: 7-8-9 bamboo
            make_suited(Suit.BAMBOO, 7),
            make_suited(Suit.BAMBOO, 8),
            make_suited(Suit.BAMBOO, 9),
            # Pong: 3x East wind
            make_wind(Wind.EAST),
            make_wind(Wind.EAST),
            make_wind(Wind.EAST),
            # Pair: Red dragon
            make_dragon(Dragon.RED),
            make_dragon(Dragon.RED),
        ]
        results = check_win(concealed, [])
        assert len(results) >= 1

    def test_non_winning_hand(self) -> None:
        concealed = [
            make_suited(Suit.BAMBOO, 1),
            make_suited(Suit.BAMBOO, 2),
            make_suited(Suit.BAMBOO, 4),  # gap
            make_suited(Suit.BAMBOO, 5),
            make_suited(Suit.BAMBOO, 6),
            make_suited(Suit.BAMBOO, 7),
            make_suited(Suit.DOTS, 1),
            make_suited(Suit.DOTS, 3),
            make_suited(Suit.DOTS, 5),
            make_suited(Suit.DOTS, 7),
            make_suited(Suit.DOTS, 9),
            make_wind(Wind.EAST),
            make_wind(Wind.SOUTH),
            make_wind(Wind.WEST),
        ]
        results = check_win(concealed, [])
        assert len(results) == 0

    def test_with_exposed_melds(self) -> None:
        """1 exposed pong + 3 concealed melds + pair."""
        exposed = [make_pong(make_wind(Wind.EAST))]
        concealed = [
            make_suited(Suit.BAMBOO, 1),
            make_suited(Suit.BAMBOO, 2),
            make_suited(Suit.BAMBOO, 3),
            make_suited(Suit.DOTS, 4),
            make_suited(Suit.DOTS, 5),
            make_suited(Suit.DOTS, 6),
            make_suited(Suit.CHARACTERS, 7),
            make_suited(Suit.CHARACTERS, 8),
            make_suited(Suit.CHARACTERS, 9),
            make_dragon(Dragon.RED),
            make_dragon(Dragon.RED),
        ]
        results = check_win(concealed, exposed)
        assert len(results) >= 1

    def test_all_pongs(self) -> None:
        """4 pongs + pair."""
        concealed = [
            make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 1),
            make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 5),
            make_suited(Suit.CHARACTERS, 9), make_suited(Suit.CHARACTERS, 9), make_suited(Suit.CHARACTERS, 9),
            make_wind(Wind.NORTH), make_wind(Wind.NORTH), make_wind(Wind.NORTH),
            make_dragon(Dragon.GREEN), make_dragon(Dragon.GREEN),
        ]
        results = check_win(concealed, [])
        assert len(results) >= 1


class TestThirteenOrphans:
    def test_valid(self) -> None:
        concealed = [
            make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 9),
            make_suited(Suit.CHARACTERS, 1), make_suited(Suit.CHARACTERS, 9),
            make_suited(Suit.DOTS, 1), make_suited(Suit.DOTS, 9),
            make_wind(Wind.EAST), make_wind(Wind.SOUTH),
            make_wind(Wind.WEST), make_wind(Wind.NORTH),
            make_dragon(Dragon.RED), make_dragon(Dragon.GREEN),
            make_dragon(Dragon.WHITE),
            make_suited(Suit.BAMBOO, 1),  # duplicate
        ]
        pair = is_thirteen_orphans(concealed, [])
        assert pair is not None
        assert pair == make_suited(Suit.BAMBOO, 1)

    def test_invalid_missing_tile(self) -> None:
        concealed = [
            make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 9),
            make_suited(Suit.CHARACTERS, 1), make_suited(Suit.CHARACTERS, 9),
            make_suited(Suit.DOTS, 1), make_suited(Suit.DOTS, 9),
            make_wind(Wind.EAST), make_wind(Wind.SOUTH),
            make_wind(Wind.WEST), make_wind(Wind.NORTH),
            make_dragon(Dragon.RED), make_dragon(Dragon.GREEN),
            # Missing white dragon
            make_suited(Suit.BAMBOO, 1),
            make_suited(Suit.BAMBOO, 1),
        ]
        assert is_thirteen_orphans(concealed, []) is None

    def test_invalid_with_melds(self) -> None:
        concealed = [
            make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 9),
        ]
        melds = [make_pong(make_wind(Wind.EAST))]
        assert is_thirteen_orphans(concealed, melds) is None

    def test_check_win_includes_orphans(self) -> None:
        concealed = [
            make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 9),
            make_suited(Suit.CHARACTERS, 1), make_suited(Suit.CHARACTERS, 9),
            make_suited(Suit.DOTS, 1), make_suited(Suit.DOTS, 9),
            make_wind(Wind.EAST), make_wind(Wind.SOUTH),
            make_wind(Wind.WEST), make_wind(Wind.NORTH),
            make_dragon(Dragon.RED), make_dragon(Dragon.GREEN),
            make_dragon(Dragon.WHITE),
            make_wind(Wind.EAST),  # duplicate
        ]
        results = check_win(concealed, [])
        assert any(len(d.melds) == 0 for d in results)
