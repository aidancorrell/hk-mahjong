"""Tests for tile definitions."""

import pytest

from hk_mahjong.core.tiles import (
    BonusType,
    Dragon,
    Suit,
    Tile,
    Wind,
    create_full_tileset,
    make_bonus,
    make_dragon,
    make_suited,
    make_wind,
    sort_tiles,
)


class TestTile:
    def test_suited_tile(self) -> None:
        t = make_suited(Suit.BAMBOO, 3)
        assert t.suit == Suit.BAMBOO
        assert t.rank == 3
        assert t.is_suited
        assert not t.is_honor
        assert not t.is_bonus

    def test_terminal(self) -> None:
        assert make_suited(Suit.DOTS, 1).is_terminal
        assert make_suited(Suit.DOTS, 9).is_terminal
        assert not make_suited(Suit.DOTS, 5).is_terminal

    def test_simple(self) -> None:
        assert make_suited(Suit.CHARACTERS, 5).is_simple
        assert not make_suited(Suit.CHARACTERS, 1).is_simple
        assert not make_suited(Suit.CHARACTERS, 9).is_simple

    def test_wind_tile(self) -> None:
        t = make_wind(Wind.EAST)
        assert t.wind == Wind.EAST
        assert t.is_honor
        assert not t.is_suited
        assert t.is_terminal_or_honor

    def test_dragon_tile(self) -> None:
        t = make_dragon(Dragon.RED)
        assert t.dragon == Dragon.RED
        assert t.is_honor

    def test_bonus_tile(self) -> None:
        t = make_bonus(BonusType.FLOWER, 1)
        assert t.is_bonus
        assert not t.is_suited
        assert not t.is_honor

    def test_frozen(self) -> None:
        t = make_suited(Suit.BAMBOO, 1)
        with pytest.raises(AttributeError):
            t.rank = 2  # type: ignore[misc]

    def test_hashable(self) -> None:
        t1 = make_suited(Suit.BAMBOO, 1)
        t2 = make_suited(Suit.BAMBOO, 1)
        assert t1 == t2
        assert hash(t1) == hash(t2)
        s = {t1, t2}
        assert len(s) == 1

    def test_short_name(self) -> None:
        assert make_suited(Suit.BAMBOO, 3).short_name() == "3B"
        assert make_suited(Suit.CHARACTERS, 7).short_name() == "7C"
        assert make_suited(Suit.DOTS, 1).short_name() == "1D"
        assert make_wind(Wind.EAST).short_name() == "EW"
        assert make_dragon(Dragon.RED).short_name() == "RD"
        assert make_bonus(BonusType.FLOWER, 2).short_name() == "F2"

    def test_invalid_rank(self) -> None:
        with pytest.raises(ValueError):
            Tile(suit=Suit.BAMBOO, rank=0)
        with pytest.raises(ValueError):
            Tile(suit=Suit.BAMBOO, rank=10)

    def test_invalid_empty(self) -> None:
        with pytest.raises(ValueError):
            Tile()

    def test_sort_tiles(self) -> None:
        tiles = [
            make_wind(Wind.EAST),
            make_suited(Suit.DOTS, 5),
            make_suited(Suit.BAMBOO, 1),
            make_dragon(Dragon.RED),
        ]
        sorted_t = sort_tiles(tiles)
        assert sorted_t[0] == make_suited(Suit.BAMBOO, 1)
        assert sorted_t[-1] == make_dragon(Dragon.RED)


class TestTileset:
    def test_full_tileset_count(self) -> None:
        tiles = create_full_tileset()
        assert len(tiles) == 144

    def test_suited_counts(self) -> None:
        tiles = create_full_tileset()
        for suit in Suit:
            for rank in range(1, 10):
                count = sum(1 for t in tiles if t.suit == suit and t.rank == rank)
                assert count == 4, f"{suit.name} {rank} should have 4 copies"

    def test_wind_counts(self) -> None:
        tiles = create_full_tileset()
        for wind in Wind:
            count = sum(1 for t in tiles if t.wind == wind)
            assert count == 4

    def test_dragon_counts(self) -> None:
        tiles = create_full_tileset()
        for dragon in Dragon:
            count = sum(1 for t in tiles if t.dragon == dragon)
            assert count == 4

    def test_bonus_counts(self) -> None:
        tiles = create_full_tileset()
        flowers = [t for t in tiles if t.bonus_type == BonusType.FLOWER]
        seasons = [t for t in tiles if t.bonus_type == BonusType.SEASON]
        assert len(flowers) == 4
        assert len(seasons) == 4
