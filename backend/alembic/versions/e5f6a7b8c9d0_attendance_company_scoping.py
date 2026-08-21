"""attendance_company_scoping

Revision ID: e5f6a7b8c9d0
Revises: d2e3f4a5b6c7
Create Date: 2026-08-11 09:30:00.000000

Adds company_id to attendance_records so every attendance row is scoped
to its owning company (multi-tenant isolation for HR).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('attendance_records') as batch_op:
        batch_op.add_column(
            sa.Column('company_id', sa.Integer(), nullable=False, server_default=sa.text('0'))
        )
        batch_op.create_foreign_key(
            op.f('fk_attendance_records_company_id_companies'),
            'companies',
            ['company_id'],
            ['id'],
            ondelete='CASCADE',
        )
        batch_op.create_index(
            op.f('ix_attendance_records_company_id'), ['company_id']
        )


def downgrade() -> None:
    with op.batch_alter_table('attendance_records') as batch_op:
        batch_op.drop_index(op.f('ix_attendance_records_company_id'))
        batch_op.drop_constraint(
            op.f('fk_attendance_records_company_id_companies'), type_='foreignkey'
        )
        batch_op.drop_column('company_id')
