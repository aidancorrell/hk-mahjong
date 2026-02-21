"""Input prompts for the game UI."""

from __future__ import annotations

from hk_mahjong.core.rules import ClaimType


def claim_prompt_text(valid_claims: list[ClaimType]) -> str:
    """Build the claim prompt string."""
    parts: list[str] = []
    if ClaimType.WIN in valid_claims:
        parts.append("[w] Win")
    if ClaimType.KONG in valid_claims:
        parts.append("[k] Kong")
    if ClaimType.PONG in valid_claims:
        parts.append("[p] Pong")
    if ClaimType.CHOW in valid_claims:
        parts.append("[c] Chow")
    parts.append("[n] Pass")
    return "  ".join(parts)


def parse_claim_key(key: str, valid_claims: list[ClaimType]) -> ClaimType | None:
    """Parse a keypress into a claim type."""
    mapping = {
        "w": ClaimType.WIN,
        "k": ClaimType.KONG,
        "p": ClaimType.PONG,
        "c": ClaimType.CHOW,
        "n": ClaimType.PASS,
    }
    claim = mapping.get(key.lower())
    if claim is None:
        return None
    if claim == ClaimType.PASS:
        return claim
    if claim in valid_claims:
        return claim
    return None


def kong_prompt_text() -> str:
    return "[k] Declare Kong  [d] Discard instead"


def win_prompt_text() -> str:
    return "[w] Declare Win!  [d] Discard instead"


def chow_select_text(options: list[tuple[str, str]]) -> str:
    """Show chow options for selection."""
    parts = [f"[{i+1}] {a}+{b}" for i, (a, b) in enumerate(options)]
    parts.append("[n] Cancel")
    return "Chow with: " + "  ".join(parts)
