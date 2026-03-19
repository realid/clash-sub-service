from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Node:
    name: str
    data: dict[str, object]
