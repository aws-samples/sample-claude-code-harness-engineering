"""A very small web framework: routes, rate limits and requests. app/server.py serves it."""
from __future__ import annotations

import functools
import inspect
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Request:
    method: str
    path: str
    query: dict = field(default_factory=dict)
    form: dict = field(default_factory=dict)
    world: object = None  # the app's state: see app/state.py


@dataclass
class Redirect:
    """Send the browser to another page, with a message to show there."""
    location: str
    message: str = ""


class TooManyRequests(Exception):
    """A route's rate limit was hit."""


class _App:
    def __init__(self) -> None:
        self.routes: dict = {}

    def route(self, path: str, methods: tuple = ("GET",)):
        def register(fn):
            for method in methods:
                self.routes[(method, path)] = fn
            return fn
        return register

    def handle(self, request: Request):
        handler = self.routes.get((request.method, request.path))
        if handler is None:
            raise LookupError(f"no route for {request.method} {request.path}")
        return handler(request) if inspect.signature(handler).parameters else handler()


def rate_limit(per_minute: int = 60):
    """Refuse a route's calls beyond per_minute in any sixty seconds."""
    def wrap(fn):
        calls: deque = deque()

        @functools.wraps(fn)
        def limited(*args, **kwargs):
            now = time.monotonic()
            while calls and now - calls[0] > 60:
                calls.popleft()
            if len(calls) >= per_minute:
                raise TooManyRequests(fn.__name__)
            calls.append(now)
            return fn(*args, **kwargs)
        return limited
    return wrap


app = _App()
