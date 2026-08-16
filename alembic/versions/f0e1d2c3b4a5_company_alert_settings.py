"""company_alert_settings

Revision ID: f0e1d2c3b4a5
Revises: e5f6a7b8c9d0
Create Date: 2026-08-15 10:00:00.000000

Adds the company-level stock alert settings columns to company_settings:
  - low_stock_threshold     default threshold for low-stock alerts
  - alert_emails            comma-separated recipients for alert emails
  - block_negative_stock    whether sales are blocked at zero stock
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0e1d2c3b4a5'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'company_settings',
        sa.Column(
            'low_stock_threshold',
            sa.Numeric(12, 4),
            nullable=False,
            server_default=sa.text('0'),
        ),
    )
    op.add_column(
        'company_settings',
        sa.Column('alert_emails', sa.String(length=1000), nullable=True),
    )
    op.add_column(
        'company_settings',
        sa.Column(
            'block_negative_stock',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
    )


def downgrade() -> None:
    op.drop_column('company_settings', 'block_negative_stock')
    op.drop_column('company_settings', 'alert_emails')
    op.drop_column('company_settings', 'low_stock_threshold')
