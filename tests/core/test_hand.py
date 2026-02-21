"""Tests for hand management."""

from hk_mahjong.core.hand import Hand
from hk_mahjong.core.meld import MeldType
from hk_mahjong.core.tiles import Suit, Wind, make_suited, make_wind


class TestHand:
    def test_add_remove(self) -> None:
        h = Hand()
        t = make_suited(Suit.BAMBOO, 3)
        h.add(t)
        assert len(h.concealed) == 1
        h.remove(t)
        assert len(h.concealed) == 0

    def test_can_pong(self) -> None:
        h = Hand()
        t = make_suited(Suit.DOTS, 5)
        h.add(t)
        assert not h.can_pong(t)
        h.add(t)
        assert h.can_pong(t)

    def test_can_kong(self) -> None:
        h = Hand()
        t = make_wind(Wind.EAST)
        for _ in range(3):
            h.add(t)
        assert h.can_kong(t)

    def test_can_chow(self) -> None:
        h = Hand()
        h.add(make_suited(Suit.BAMBOO, 4))
        h.add(make_suited(Suit.BAMBOO, 5))
        chows = h.can_chow(make_suited(Suit.BAMBOO, 3))
        assert len(chows) >= 1

    def test_can_chow_honor_returns_empty(self) -> None:
        h = Hand()
        h.add(make_suited(Suit.BAMBOO, 4))
        h.add(make_suited(Suit.BAMBOO, 5))
        assert h.can_chow(make_wind(Wind.EAST)) == []

    def test_declare_pong(self) -> None:
        h = Hand()
        t = make_suited(Suit.DOTS, 7)
        h.add(t)
        h.add(t)
        h.add(make_suited(Suit.BAMBOO, 1))
        meld = h.declare_pong(t)
        assert meld.meld_type == MeldType.PONG
        assert len(h.concealed) == 1
        assert len(h.melds) == 1

    def test_declare_kong(self) -> None:
        h = Hand()
        t = make_suited(Suit.CHARACTERS, 9)
        for _ in range(3):
            h.add(t)
        meld = h.declare_kong(t)
        assert meld.is_kong
        assert len(h.concealed) == 0
        assert len(h.melds) == 1

    def test_declare_concealed_kong(self) -> None:
        h = Hand()
        t = make_suited(Suit.BAMBOO, 2)
        for _ in range(4):
            h.add(t)
        meld = h.declare_concealed_kong(t)
        assert meld.meld_type == MeldType.CONCEALED_KONG
        assert len(h.concealed) == 0

    def test_promote_kong(self) -> None:
        h = Hand()
        t = make_suited(Suit.DOTS, 3)
        h.add(t)
        h.add(t)
        h.declare_pong(t)
        # Now add one more and promote
        h.add(t)
        meld = h.promote_kong(t)
        assert meld.is_kong
        assert len(h.melds) == 1
        assert h.melds[0].meld_type == MeldType.KONG

    def test_declare_chow(self) -> None:
        h = Hand()
        h.add(make_suited(Suit.BAMBOO, 2))
        h.add(make_suited(Suit.BAMBOO, 3))
        h.add(make_suited(Suit.DOTS, 5))

        claimed = make_suited(Suit.BAMBOO, 1)
        companions = (make_suited(Suit.BAMBOO, 2), make_suited(Suit.BAMBOO, 3))
        meld = h.declare_chow(claimed, companions)
        assert meld.is_chow
        assert len(h.concealed) == 1  # only dots 5 left
        assert len(h.melds) == 1

    def test_can_self_kong(self) -> None:
        h = Hand()
        t = make_suited(Suit.BAMBOO, 5)
        for _ in range(4):
            h.add(t)
        result = h.can_self_kong()
        assert t in result
