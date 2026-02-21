"""Tests for wall management."""

from hk_mahjong.core.wall import Wall, WallExhaustedError
import pytest


class TestWall:
    def test_initial_counts(self) -> None:
        wall = Wall(seed=42)
        # 144 total - 14 dead wall = 130 live
        assert wall.tiles_remaining == 130
        assert wall.dead_wall_remaining == 14

    def test_draw(self) -> None:
        wall = Wall(seed=42)
        t = wall.draw()
        assert t is not None
        assert wall.tiles_remaining == 129

    def test_draw_replacement(self) -> None:
        wall = Wall(seed=42)
        t = wall.draw_replacement()
        assert t is not None
        assert wall.dead_wall_remaining == 13

    def test_deal(self) -> None:
        wall = Wall(seed=42)
        hands = wall.deal()
        assert len(hands) == 4
        for h in hands:
            assert len(h) == 13
        # 52 tiles dealt from 130 = 78 remaining
        assert wall.tiles_remaining == 78

    def test_reproducible(self) -> None:
        w1 = Wall(seed=123)
        w2 = Wall(seed=123)
        for _ in range(10):
            assert w1.draw() == w2.draw()

    def test_exhaust(self) -> None:
        wall = Wall(seed=42)
        while not wall.is_exhausted:
            wall.draw()
        with pytest.raises(WallExhaustedError):
            wall.draw()
