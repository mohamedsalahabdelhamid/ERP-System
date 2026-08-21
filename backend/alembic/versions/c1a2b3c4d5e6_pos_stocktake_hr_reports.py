"""pos_stocktake_hr_reports

Revision ID: c1a2b3c4d5e6
Revises: 9f0a9c90aa37
Create Date: 2026-08-10 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3c4d5e6'
down_revision: Union[str, None] = '9f0a9c90aa37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- POS (spec 6.3) ----
    op.create_table('pos_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('branch_id', sa.Integer(), nullable=True),
    sa.Column('opened_by', sa.Integer(), nullable=False),
    sa.Column('opened_at', sa.String(length=30), nullable=False),
    sa.Column('closed_at', sa.String(length=30), nullable=True),
    sa.Column('opening_cash', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('closing_cash', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('expected_cash', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('variance', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name=op.f('fk_pos_sessions_branch_id_branches'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_pos_sessions_company_id_companies'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pos_sessions'))
    )
    op.create_index(op.f('ix_pos_sessions_company_id'), 'pos_sessions', ['company_id'], unique=False)
    op.create_table('pos_orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('invoice_id', sa.Integer(), nullable=True),
    sa.Column('order_number', sa.String(length=50), nullable=False),
    sa.Column('partner_id', sa.Integer(), nullable=True),
    sa.Column('cashier_id', sa.Integer(), nullable=False),
    sa.Column('total', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_pos_orders_company_id_companies'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['invoice_id'], ['sales_invoices.id'], name=op.f('fk_pos_orders_invoice_id_sales_invoices'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], name=op.f('fk_pos_orders_partner_id_partners'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['session_id'], ['pos_sessions.id'], name=op.f('fk_pos_orders_session_id_pos_sessions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pos_orders'))
    )
    op.create_index(op.f('ix_pos_orders_company_id'), 'pos_orders', ['company_id'], unique=False)
    op.create_index(op.f('ix_pos_orders_session_id'), 'pos_orders', ['session_id'], unique=False)
    op.create_table('pos_order_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('line_total', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], name=op.f('fk_pos_order_lines_item_id_items'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['order_id'], ['pos_orders.id'], name=op.f('fk_pos_order_lines_order_id_pos_orders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pos_order_lines'))
    )
    op.create_index(op.f('ix_pos_order_lines_item_id'), 'pos_order_lines', ['item_id'], unique=False)
    op.create_index(op.f('ix_pos_order_lines_order_id'), 'pos_order_lines', ['order_id'], unique=False)

    # ---- Stock taking (spec Phase 6.3) ----
    op.create_table('stock_takes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('warehouse_id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('posted_at', sa.String(length=30), nullable=True),
    sa.Column('note', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_stock_takes_company_id_companies'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], name=op.f('fk_stock_takes_warehouse_id_warehouses'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stock_takes'))
    )
    op.create_index(op.f('ix_stock_takes_company_id'), 'stock_takes', ['company_id'], unique=False)
    op.create_index(op.f('ix_stock_takes_warehouse_id'), 'stock_takes', ['warehouse_id'], unique=False)
    op.create_table('stock_take_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stock_take_id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('book_qty', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('counted_qty', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('diff_qty', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('adjustment_value', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], name=op.f('fk_stock_take_lines_item_id_items'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['stock_take_id'], ['stock_takes.id'], name=op.f('fk_stock_take_lines_stock_take_id_stock_takes'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stock_take_lines'))
    )
    op.create_index(op.f('ix_stock_take_lines_item_id'), 'stock_take_lines', ['item_id'], unique=False)
    op.create_index(op.f('ix_stock_take_lines_stock_take_id'), 'stock_take_lines', ['stock_take_id'], unique=False)

    # ---- HR leave requests (spec Phase 8) ----
    op.create_table('leave_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('leave_type', sa.String(length=50), nullable=False),
    sa.Column('start_date', sa.String(length=20), nullable=False),
    sa.Column('end_date', sa.String(length=20), nullable=False),
    sa.Column('days', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('reason', sa.String(length=500), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_leave_requests_company_id_companies'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name=op.f('fk_leave_requests_employee_id_employees'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_leave_requests'))
    )
    op.create_index(op.f('ix_leave_requests_company_id'), 'leave_requests', ['company_id'], unique=False)
    op.create_index(op.f('ix_leave_requests_employee_id'), 'leave_requests', ['employee_id'], unique=False)

    # ---- Payments (spec 5.1) — the table was never created by earlier
    # migrations, so create it here including the FX settlement columns ----
    op.create_table('payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('partner_id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=False),
    sa.Column('document_type', sa.String(length=50), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('payment_date', sa.String(length=30), nullable=True),
    sa.Column('amount', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('currency_code', sa.String(length=10), nullable=False),
    sa.Column('fx_rate_used', sa.Numeric(precision=18, scale=8), nullable=False, server_default='1'),
    sa.Column('base_amount', sa.Numeric(precision=18, scale=4), nullable=False, server_default='0'),
    sa.Column('fx_gain_loss', sa.Numeric(precision=18, scale=4), nullable=False, server_default='0'),
    sa.Column('payment_method', sa.String(length=30), nullable=False),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_payments_company_id_companies'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], name=op.f('fk_payments_partner_id_partners'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payments')),
    sa.UniqueConstraint('company_id', 'reference', name=op.f('uq_payments_company_reference'))
    )
    op.create_index(op.f('ix_payments_company_id'), 'payments', ['company_id'], unique=False)
    op.create_index(op.f('ix_payments_partner_id'), 'payments', ['partner_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_partner_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_company_id'), table_name='payments')
    op.drop_table('payments')

    op.drop_index(op.f('ix_leave_requests_employee_id'), table_name='leave_requests')
    op.drop_index(op.f('ix_leave_requests_company_id'), table_name='leave_requests')
    op.drop_table('leave_requests')

    op.drop_index(op.f('ix_stock_take_lines_stock_take_id'), table_name='stock_take_lines')
    op.drop_index(op.f('ix_stock_take_lines_item_id'), table_name='stock_take_lines')
    op.drop_table('stock_take_lines')
    op.drop_index(op.f('ix_stock_takes_warehouse_id'), table_name='stock_takes')
    op.drop_index(op.f('ix_stock_takes_company_id'), table_name='stock_takes')
    op.drop_table('stock_takes')

    op.drop_index(op.f('ix_pos_order_lines_order_id'), table_name='pos_order_lines')
    op.drop_index(op.f('ix_pos_order_lines_item_id'), table_name='pos_order_lines')
    op.drop_table('pos_order_lines')
    op.drop_index(op.f('ix_pos_orders_session_id'), table_name='pos_orders')
    op.drop_index(op.f('ix_pos_orders_company_id'), table_name='pos_orders')
    op.drop_table('pos_orders')
    op.drop_index(op.f('ix_pos_sessions_company_id'), table_name='pos_sessions')
    op.drop_table('pos_sessions')
