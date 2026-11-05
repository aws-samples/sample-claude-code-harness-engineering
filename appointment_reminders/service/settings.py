"""Tunable numbers for the reminder service."""
from __future__ import annotations

REQUEST_TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2
# Messaging contract: 150 sends a minute. 120 leaves room for one-off messages.
MAX_SENDS_PER_MINUTE = 120
REMINDER_WINDOW_SECONDS = 3600
SWEEP_LIMIT = 200
BATCH_SIZE = 25
JITTER = 0.62
