# HK Mahjong

A terminal-based Hong Kong style mahjong game. Play against 3 AI opponents in your terminal.

## Features

- Full Hong Kong mahjong rules (4-player)
- Switchable Unicode/ASCII tile rendering (press `r` during game)
- Shanten-based AI opponents
- HK faan scoring with 3-faan minimum
- Special hands: Thirteen Orphans, Nine Gates, Great Dragons/Winds, and more

## Installation

```bash
pip install .
```

## Usage

```bash
# Run with Unicode tiles (default)
hk-mahjong

# Run with ASCII tiles
hk-mahjong --ascii

# Run as module
python -m hk_mahjong

# Reproducible game with seed
hk-mahjong --seed 42
```

## Controls

| Key | Action |
|-----|--------|
| `←` / `→` | Select tile |
| `Enter` | Confirm discard |
| `w` | Declare win |
| `p` | Claim pong |
| `k` | Claim/declare kong |
| `c` | Claim chow |
| `n` | Pass (skip claim) |
| `r` | Toggle Unicode/ASCII rendering |
| `q` | Quit |

## Scoring (Hong Kong Faan)

Minimum 3 faan required to win. Limit hand = 13 faan.

| Pattern | Faan |
|---------|------|
| Dragon Pong | 1 |
| Seat/Prevailing Wind | 1 each |
| Self Drawn | 1 |
| No Flowers | 1 |
| Fully Concealed | 1 |
| All Pongs | 3 |
| Mixed One Suit | 3 |
| Pure One Suit | 7 |
| Thirteen Orphans | 13 (limit) |
| Great Dragons | 13 (limit) |
| Great Winds | 13 (limit) |
| All Honors | 13 (limit) |
| Nine Gates | 13 (limit) |

## Development

```bash
# Install dev dependencies
pip install -e . pytest ruff mypy

# Run tests
pytest

# Lint
ruff check src/

# Type check
mypy src/
```

## License

MIT
