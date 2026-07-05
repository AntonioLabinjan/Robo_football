"""Formation layouts defining relative home positions (0..1 field-normalized)."""
from __future__ import annotations
from typing import List, Tuple

# Each formation: list of (x_frac, y_frac) for 5 outfield roles (attacking to the right).
# x_frac in [0,1] along own->opponent goal axis, y_frac in [0,1] across field width.
FORMATION_LAYOUTS = {
    "2-2-1": [
        (0.12, 0.5),   # goalkeeper-ish deep back
        (0.28, 0.25),
        (0.28, 0.75),
        (0.55, 0.30),
        (0.55, 0.70),
    ],
    "1-3-1": [
        (0.15, 0.5),
        (0.40, 0.20),
        (0.40, 0.5),
        (0.40, 0.80),
        (0.65, 0.5),
    ],
    "2-1-2": [
        (0.20, 0.30),
        (0.20, 0.70),
        (0.45, 0.5),
        (0.65, 0.25),
        (0.65, 0.75),
    ],
}


def get_layout(name: str) -> List[Tuple[float, float]]:
    return FORMATION_LAYOUTS.get(name, FORMATION_LAYOUTS["2-2-1"])
