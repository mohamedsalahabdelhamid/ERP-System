"""platform_tenant_models

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3c4d5e6
Create Date: 2026-08-10 11:00:00.000000

Adds the SaaS/tenant platform fields:
  - users.is_superuser          (platform owner flag)
  - companies.subdomain         (unique tenant subdomain)
  - companies.status            (active / trial / suspended)
  - company_settings.max_users  (licensed seat count per tenant)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'is_superuser',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )

    # batch mode: SQLite cannot ALTER constraints, so the whole companies table
    # change (add columns + unique constraint) is performed copy-and-move.
    with op.batch_alter_table('companies') as batch_op:
        batch_op.add_column(
            sa.Column('subdomain', sa.String(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                'status',
                sa.String(length=20),
                nullable=False,
                server_default=sa.text("'active'"),
            ),
        )
        batch_op.create_unique_constraint(
            op.f('uq_companies_subdomain'), ['subdomain']
        )

    op.add_column(
        'company_settings',
        sa.Column(
            'max_users',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('5'),
        ),
    )


def downgrade() -> None:
    op.drop_column('company_settings', 'max_users')
    with op.batch_alter_table('companies') as batch_op:
        batch_op.drop_constraint(
            op.f('uq_companies_subdomain'), type_='unique'
        )
        batch_op.drop_column('status')
        batch_op.drop_column('subdomain')
    op.drop_column('users', 'is_superuser')
