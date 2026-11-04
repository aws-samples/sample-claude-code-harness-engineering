"""Finding records, saving profiles, running branch checks."""
from __future__ import annotations

import logging

from appointment_reminders.service.models import BranchCheck, CustomerProfile

logger = logging.getLogger(__name__)


def find_profile(record: CustomerProfile, candidates: list[CustomerProfile]) -> CustomerProfile | None:
    """Find the one candidate with this record's reference."""
    hits = [c for c in candidates if c.ref == record.ref]
    if len(hits) != 1:
        logger.warning("record %s matched %d candidates", record.ref, len(hits))
    return hits[0] if hits else None


def save_profile(record: CustomerProfile, store) -> None:
    store.save(record)


def run_branch_check(check: BranchCheck) -> bool:
    return check.passed


class BranchStore:
    def __init__(self, db) -> None:
        self.db = db

    def validate_settings(self, branch: str) -> bool:
        settings = self.db.fetch_settings(branch)
        return "region" in settings and "owner" in settings


def load_customer(db, customer_ref: str) -> dict:
    return db.upsert("customers", {"ref": customer_ref})
