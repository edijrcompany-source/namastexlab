"""ULID — 26 chars Crockford Base32 (contrato: ^[0-9A-HJKMNP-TV-Z]{26}$)."""

from __future__ import annotations

import os
import time

_ALFABETO = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def ulid() -> str:
    """48 bits de timestamp (ms) + 80 bits de aleatoriedade — ordenável."""
    ms = int(time.time() * 1000)
    rand = os.urandom(10)
    valor = (ms << 80) | int.from_bytes(rand, "big")
    return "".join(_ALFABETO[(valor >> shift) & 31] for shift in range(125, -1, -5))
