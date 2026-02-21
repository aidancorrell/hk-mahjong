"""Tests for meld types."""

import pytest

from hk_mahjong.core.meld import (
    Meld,
    MeldType,
    make_chow,
    make_kong,
    make_pong,
)
from hk_mahjong.core.tiles import Suit, Wind, make_suited, make_wind


class TestMeld:
    def test_chow(self) -> None:
        t1 = make_suited(Suit.BAMBOO, 3)
        t2 = make_suited(Suit.BAMBOO, 4)
        t3 = make_suited(Suit.BAMBOO, 5)
        meld = make_chow(t3, t1, t2)  # out of order
        assert meld.meld_type == MeldType.CHOW
        assert meld.tiles[0].rank == 3  # auto-sorted
        assert meld.is_chow

    def test_pong(self) -> None:
        t = make_suited(Suit.DOTS, 7)
        meld = make_pong(t)
        assert meld.meld_type == MeldType.PONG
        assert len(meld.tiles) == 3
        assert meld.is_pong

    def test_kong(self) -> None:
        t = make_wind(Wind.EAST)
        meld = make_kong(t)
        assert meld.meld_type == MeldType.KONG
        assert len(meld.tiles) == 4
        assert meld.is_kong

    def test_concealed_kong(self) -> None:
        t = make_suited(Suit.CHARACTERS, 1)
        meld = make_kong(t, concealed=True)
        assert meld.meld_type == MeldType.CONCEALED_KONG
        assert meld.is_kong
        assert meld.is_concealed

    def test_invalid_chow_different_suits(self) -> None:
        t1 = make_suited(Suit.BAMBOO, 3)
        t2 = make_suited(Suit.DOTS, 4)
        t3 = make_suited(Suit.BAMBOO, 5)
        with pytest.raises(ValueError):
            make_chow(t1, t2, t3)

    def test_invalid_chow_non_consecutive(self) -> None:
        t1 = make_suited(Suit.BAMBOO, 3)
        t2 = make_suited(Suit.BAMBOO, 5)
        t3 = make_suited(Suit.BAMBOO, 7)
        with pytest.raises(ValueError):
            make_chow(t1, t2, t3)

    def test_invalid_chow_honor(self) -> None:
        with pytest.raises(ValueError):
            Meld(MeldType.CHOW, (make_wind(Wind.EAST), make_wind(Wind.SOUTH), make_wind(Wind.WEST)))

    def test_invalid_pong_different(self) -> None:
        with pytest.raises(ValueError):
            Meld(MeldType.PONG, (
                make_suited(Suit.BAMBOO, 1),
                make_suited(Suit.BAMBOO, 1),
                make_suited(Suit.BAMBOO, 2),
            ))
