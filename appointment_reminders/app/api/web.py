"""A very small stand-in for a web framework."""
from __future__ import annotations


class _App:
    def route(self, path: str):
        return lambda fn: fn


def rate_limit(per_minute: int = 60):
    return lambda fn: fn


app = _App()
