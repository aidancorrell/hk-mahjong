"""CLI entry point for HK Mahjong."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Hong Kong Mahjong - Terminal Game")
    parser.add_argument(
        "--ascii", action="store_true", help="Use ASCII tile rendering instead of Unicode"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for reproducible games"
    )
    args = parser.parse_args()

    from hk_mahjong.ui.app import App

    app = App(use_unicode=not args.ascii, seed=args.seed)
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
