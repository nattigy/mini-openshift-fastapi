"""Add environments and deployments tables

Revision ID: 7a9d3e5f8b2c
Revises: 6feb3622ce30
Create Date: 2025-12-06 17:54:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7a9d3e5f8b2c'
down_revision: Union[str, None] = '6feb3622ce30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create environments table
    op.create_table('environments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('subdomain_prefix', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_environments_name'), 'environments', ['name'], unique=True)

    # Seed default environments
    op.execute("""
        INSERT INTO environments (id, name, subdomain_prefix, description, created_at, updated_at) VALUES
        (gen_random_uuid(), 'Production', '', 'Production environment', NOW(), NOW()),
        (gen_random_uuid(), 'UAT', 'uat', 'User Acceptance Testing environment', NOW(), NOW()),
        (gen_random_uuid(), 'Dev', 'dev', 'Development environment', NOW(), NOW())
    """)

    # Add domain column to projects table
    op.add_column('projects', sa.Column('domain', sa.String(length=255), nullable=True))

    # Create deployments table
    op.create_table('deployments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subdomain', sa.String(length=100), nullable=False),
        sa.Column('image', sa.String(), nullable=False),
        sa.Column('replicas', sa.Integer(), nullable=True),
        sa.Column('image_pull_policy', sa.String(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('environment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop deployments table
    op.drop_table('deployments')
    
    # Remove domain column from projects
    op.drop_column('projects', 'domain')
    
    # Drop environments table
    op.drop_index(op.f('ix_environments_name'), table_name='environments')
    op.drop_table('environments')
