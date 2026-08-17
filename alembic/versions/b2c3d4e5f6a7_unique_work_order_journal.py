"""unique_work_order_journal

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-16 12:00:00.000000

Adds per-company unique constraints on entity codes/numbering that were
previously only guarded in application code:
  - work_orders     (company_id, number)
  - journal_entries (company_id, reference)

Implemented as unique indexes (rather than ALTER TABLE ADD CONSTRAINT) so the
same migration runs on both PostgreSQL and SQLite.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'uq_work_orders_company_number',
        'work_orders',
        ['company_id', 'number'],
        unique=True,
    )
    op.create_index(
        'uq_journal_entries_company_reference',
        'journal_entries',
        ['company_id', 'reference'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('uq_journal_entries_company_reference', table_name='journal_entries')
    op.drop_index('uq_work_orders_company_number', table_name='work_orders')
