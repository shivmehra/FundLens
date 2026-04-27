"""Initial migration

Revision ID: c2aa7b608db5
Revises: 
Create Date: 2026-04-27 12:08:01.856920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2aa7b608db5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create funds table
    op.create_table(
        'funds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('inception_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_funds_name', 'funds', ['name'])

    # Create nav_history table
    op.create_table(
        'nav_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('nav', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fund_id', 'date', name='uq_nav_history_fund_date'),
    )
    op.create_index('ix_nav_history_fund_id', 'nav_history', ['fund_id'])
    op.create_index('ix_nav_history_date', 'nav_history', ['date'])

    # Create fund_metadata table
    op.create_table(
        'fund_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.Integer(), nullable=False),
        sa.Column('manager', sa.String(length=255), nullable=True),
        sa.Column('allocation', sa.Text(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('cagr', sa.Float(), nullable=True),
        sa.Column('aum', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fund_id'),
    )

    # Create upload_jobs table
    op.create_table(
        'upload_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('imported_count', sa.Integer(), nullable=False),
        sa.Column('rejected_count', sa.Integer(), nullable=False),
        sa.Column('error_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_upload_jobs_status', 'upload_jobs', ['status'])
    op.create_index('ix_upload_jobs_created_at', 'upload_jobs', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('ix_upload_jobs_created_at', 'upload_jobs')
    op.drop_index('ix_upload_jobs_status', 'upload_jobs')
    op.drop_index('ix_nav_history_date', 'nav_history')
    op.drop_index('ix_nav_history_fund_id', 'nav_history')
    op.drop_index('ix_funds_name', 'funds')

    # Drop tables
    op.drop_table('upload_jobs')
    op.drop_table('fund_metadata')
    op.drop_table('nav_history')
    op.drop_table('funds')
