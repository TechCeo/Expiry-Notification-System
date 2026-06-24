"""Establish the backend migration baseline.

Revision ID: 20260623_0001
Revises:
Create Date: 2026-06-23
"""
from collections.abc import Sequence

revision: str = "20260623_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the baseline; domain tables arrive in the next migration."""


def downgrade() -> None:
    """The baseline intentionally has no schema objects to remove."""
