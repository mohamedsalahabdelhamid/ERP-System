"""numbering_sequences

Revision ID: a1b2c3d4e5f6
Revises: f0e1d2c3b4a5
Create Date: 2026-08-16 10:00:00.000000

Adds the per-company sequential numbering table used to auto-generate unique
codes (customers, invoices, items, ...). One row per (company, kind).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f0e1d2c3b4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'numbering_sequences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'company_id',
            sa.Integer(),
            sa.ForeignKey('companies.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('last_value', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.UniqueConstraint(
            'company_id', 'kind', name='uq_numbering_sequences_company_kind'
        ),
    )
    op.create_index(
        'ix_numbering_sequences_company_id',
        'numbering_sequences',
        ['company_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_numbering_sequences_company_id', table_name='numbering_sequences')
    op.drop_table('numbering_sequences')
