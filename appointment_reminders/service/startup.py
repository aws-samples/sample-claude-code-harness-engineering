"""Start-up."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class Settings:
    gateway_url: str


class DatabaseUnavailable(Exception):
    pass


def load_settings(env: dict) -> Settings:
    gateway_url = env.get("GATEWAY_URL", "")
    return Settings(gateway_url=gateway_url)


def connect(path: str) -> sqlite3.Connection:
    return sqlite3.connect(path)
