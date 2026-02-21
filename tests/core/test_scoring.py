"""Tests for HK faan scoring."""

from hk_mahjong.core.meld import MeldType, Meld, make_pong, make_kong
from hk_mahjong.core.scoring import ScoringContext, score_hand, LIMIT_FAAN
from hk_mahjong.core.tiles import (
    Dragon,
    Suit,
    Wind,
    make_dragon,
    make_suited,
    make_wind,
)
from hk_mahjong.core.win_check import HandDecomposition, check_win


def _make_chow_meld(suit: Suit, start: int) -> Meld:
    return Meld(
        MeldType.CHOW,
        (make_suited(suit, start), make_suited(suit, start + 1), make_suited(suit, start + 2)),
    )


class TestScoring:
    def test_dragon_pong(self) -> None:
        decomp = HandDecomposition(
            melds=(
                make_pong(make_dragon(Dragon.RED)),
                _make_chow_meld(Suit.BAMBOO, 1),
                _make_chow_meld(Suit.DOTS, 4),
                _make_chow_meld(Suit.CHARACTERS, 7),
            ),
            pair=make_suited(Suit.BAMBOO, 5),
            concealed_melds=(
                _make_chow_meld(Suit.BAMBOO, 1),
                _make_chow_meld(Suit.DOTS, 4),
                _make_chow_meld(Suit.CHARACTERS, 7),
            ),
        )
        ctx = ScoringContext(
            decomposition=decomp,
            exposed_melds=[make_pong(make_dragon(Dragon.RED))],
            concealed_tiles=[
                make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 2), make_suited(Suit.BAMBOO, 3),
                make_suited(Suit.DOTS, 4), make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 6),
                make_suited(Suit.CHARACTERS, 7), make_suited(Suit.CHARACTERS, 8), make_suited(Suit.CHARACTERS, 9),
                make_suited(Suit.BAMBOO, 5), make_suited(Suit.BAMBOO, 5),
            ],
            bonus_tiles=[],
            winning_tile=make_suited(Suit.BAMBOO, 5),
            self_drawn=False,
            seat_wind=Wind.EAST,
            prevailing_wind=Wind.EAST,
        )
        result = score_hand(ctx)
        assert any(f.name == "Red Dragon Pong" for f in result.items)

    def test_self_drawn(self) -> None:
        decomp = HandDecomposition(
            melds=(
                make_pong(make_dragon(Dragon.RED)),
                make_pong(make_dragon(Dragon.GREEN)),
                _make_chow_meld(Suit.BAMBOO, 1),
                _make_chow_meld(Suit.DOTS, 4),
            ),
            pair=make_suited(Suit.BAMBOO, 5),
            concealed_melds=(
                _make_chow_meld(Suit.BAMBOO, 1),
                _make_chow_meld(Suit.DOTS, 4),
            ),
        )
        ctx = ScoringContext(
            decomposition=decomp,
            exposed_melds=[make_pong(make_dragon(Dragon.RED)), make_pong(make_dragon(Dragon.GREEN))],
            concealed_tiles=[
                make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 2), make_suited(Suit.BAMBOO, 3),
                make_suited(Suit.DOTS, 4), make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 6),
                make_suited(Suit.BAMBOO, 5), make_suited(Suit.BAMBOO, 5),
            ],
            bonus_tiles=[],
            winning_tile=make_suited(Suit.BAMBOO, 5),
            self_drawn=True,
            seat_wind=Wind.EAST,
            prevailing_wind=Wind.EAST,
        )
        result = score_hand(ctx)
        assert any(f.name == "Self Drawn" for f in result.items)
        assert result.total_faan >= 3

    def test_all_pongs(self) -> None:
        decomp = HandDecomposition(
            melds=(
                make_pong(make_suited(Suit.BAMBOO, 1)),
                make_pong(make_suited(Suit.DOTS, 5)),
                make_pong(make_suited(Suit.CHARACTERS, 9)),
                make_pong(make_wind(Wind.NORTH)),
            ),
            pair=make_dragon(Dragon.GREEN),
            concealed_melds=(
                make_pong(make_suited(Suit.BAMBOO, 1)),
                make_pong(make_suited(Suit.DOTS, 5)),
                make_pong(make_suited(Suit.CHARACTERS, 9)),
                make_pong(make_wind(Wind.NORTH)),
            ),
        )
        ctx = ScoringContext(
            decomposition=decomp,
            exposed_melds=[],
            concealed_tiles=[
                make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 1),
                make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 5),
                make_suited(Suit.CHARACTERS, 9), make_suited(Suit.CHARACTERS, 9), make_suited(Suit.CHARACTERS, 9),
                make_wind(Wind.NORTH), make_wind(Wind.NORTH), make_wind(Wind.NORTH),
                make_dragon(Dragon.GREEN), make_dragon(Dragon.GREEN),
            ],
            bonus_tiles=[],
            winning_tile=make_dragon(Dragon.GREEN),
            self_drawn=False,
            seat_wind=Wind.SOUTH,
            prevailing_wind=Wind.EAST,
        )
        result = score_hand(ctx)
        assert any(f.name == "All Pongs" for f in result.items)

    def test_pure_one_suit(self) -> None:
        decomp = HandDecomposition(
            melds=(
                _make_chow_meld(Suit.BAMBOO, 1),
                _make_chow_meld(Suit.BAMBOO, 4),
                _make_chow_meld(Suit.BAMBOO, 7),
                make_pong(make_suited(Suit.BAMBOO, 5)),
            ),
            pair=make_suited(Suit.BAMBOO, 2),
            concealed_melds=(
                _make_chow_meld(Suit.BAMBOO, 1),
                _make_chow_meld(Suit.BAMBOO, 4),
                _make_chow_meld(Suit.BAMBOO, 7),
                make_pong(make_suited(Suit.BAMBOO, 5)),
            ),
        )
        all_tiles = []
        for m in decomp.melds:
            all_tiles.extend(m.tiles)
        all_tiles.extend([make_suited(Suit.BAMBOO, 2), make_suited(Suit.BAMBOO, 2)])

        ctx = ScoringContext(
            decomposition=decomp,
            exposed_melds=[],
            concealed_tiles=all_tiles,
            bonus_tiles=[],
            winning_tile=make_suited(Suit.BAMBOO, 2),
            self_drawn=False,
            seat_wind=Wind.SOUTH,
            prevailing_wind=Wind.EAST,
        )
        result = score_hand(ctx)
        assert any(f.name == "Pure One Suit" for f in result.items)

    def test_thirteen_orphans(self) -> None:
        concealed = [
            make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 9),
            make_suited(Suit.CHARACTERS, 1), make_suited(Suit.CHARACTERS, 9),
            make_suited(Suit.DOTS, 1), make_suited(Suit.DOTS, 9),
            make_wind(Wind.EAST), make_wind(Wind.SOUTH),
            make_wind(Wind.WEST), make_wind(Wind.NORTH),
            make_dragon(Dragon.RED), make_dragon(Dragon.GREEN),
            make_dragon(Dragon.WHITE),
            make_suited(Suit.BAMBOO, 1),
        ]
        decomps = check_win(concealed, [])
        orphan_decomp = [d for d in decomps if len(d.melds) == 0]
        assert orphan_decomp

        ctx = ScoringContext(
            decomposition=orphan_decomp[0],
            exposed_melds=[],
            concealed_tiles=concealed,
            bonus_tiles=[],
            winning_tile=make_suited(Suit.BAMBOO, 1),
            self_drawn=False,
            seat_wind=Wind.EAST,
            prevailing_wind=Wind.EAST,
        )
        result = score_hand(ctx)
        assert result.is_limit
        assert result.total_faan == LIMIT_FAAN

    def test_great_dragons(self) -> None:
        decomp = HandDecomposition(
            melds=(
                make_pong(make_dragon(Dragon.RED)),
                make_pong(make_dragon(Dragon.GREEN)),
                make_pong(make_dragon(Dragon.WHITE)),
                _make_chow_meld(Suit.BAMBOO, 1),
            ),
            pair=make_suited(Suit.DOTS, 5),
            concealed_melds=(_make_chow_meld(Suit.BAMBOO, 1),),
        )
        all_tiles = []
        for m in decomp.melds:
            all_tiles.extend(m.tiles)
        all_tiles.extend([make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 5)])

        ctx = ScoringContext(
            decomposition=decomp,
            exposed_melds=list(decomp.melds[:3]),
            concealed_tiles=[
                make_suited(Suit.BAMBOO, 1), make_suited(Suit.BAMBOO, 2), make_suited(Suit.BAMBOO, 3),
                make_suited(Suit.DOTS, 5), make_suited(Suit.DOTS, 5),
            ],
            bonus_tiles=[],
            winning_tile=make_suited(Suit.DOTS, 5),
            self_drawn=False,
            seat_wind=Wind.EAST,
            prevailing_wind=Wind.EAST,
        )
        result = score_hand(ctx)
        assert result.is_limit
        assert any(f.name == "Great Dragons" for f in result.items)
