"""personalized_planning_and_route_legs

Adds (ADR-056):
  - itineraries.is_discoverable (privacy flag, default private)
  - itinerary_participants (per-traveler age/age_band/gender)
  - itinerary_planning_profiles (normalized similarity snapshot, 1:1)
  - itinerary_items.route_* (persisted route-leg snapshot; distance and
    duration keep living in the existing travel_from_previous_* columns)

Existing itinerary rows are preserved untouched: every new itinerary
column is nullable or has a server default, and the new tables start
empty. Downgrade removes only these structures.

Revision ID: d7e2f4a9b301
Revises: c1b489a12e34
Create Date: 2026-09-26 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7e2f4a9b301'
down_revision: Union[str, Sequence[str], None] = 'c1b489a12e34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('itineraries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_discoverable', sa.Boolean(), server_default=sa.false(), nullable=False))

    with op.batch_alter_table('itinerary_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('route_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('route_source', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('route_geometry', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('route_waypoint_key', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('route_calculated_at', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'itinerary_participants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('itinerary_id', sa.String(length=36), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('age_years', sa.Integer(), nullable=False),
        sa.Column('age_band', sa.String(length=10), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('age_years >= 0 AND age_years <= 120', name='ck_itinerary_participant_age_range'),
        sa.CheckConstraint('sequence >= 1', name='ck_itinerary_participant_sequence_positive'),
        sa.ForeignKeyConstraint(['itinerary_id'], ['itineraries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('itinerary_id', 'sequence', name='uq_itinerary_participant_sequence'),
    )
    op.create_index('ix_itinerary_participants_itinerary_id', 'itinerary_participants', ['itinerary_id'], unique=False)

    op.create_table(
        'itinerary_planning_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('itinerary_id', sa.String(length=36), nullable=False),
        sa.Column('destination_key', sa.String(length=160), nullable=True),
        sa.Column('destination_label', sa.String(length=200), nullable=True),
        sa.Column('group_size', sa.Integer(), nullable=False),
        sa.Column('children_count', sa.Integer(), nullable=False),
        sa.Column('teens_count', sa.Integer(), nullable=False),
        sa.Column('adults_count', sa.Integer(), nullable=False),
        sa.Column('seniors_count', sa.Integer(), nullable=False),
        sa.Column('age_band_distribution', sa.JSON(), nullable=False),
        sa.Column('interests', sa.JSON(), nullable=False),
        sa.Column('budget_max', sa.Float(), nullable=True),
        sa.Column('pace', sa.String(length=20), nullable=False),
        sa.Column('accessibility_requirements', sa.JSON(), nullable=False),
        sa.Column('travel_mode', sa.String(length=20), nullable=False),
        sa.Column('trip_month', sa.Integer(), nullable=False),
        sa.Column('start_location_lat', sa.Float(), nullable=True),
        sa.Column('start_location_lng', sa.Float(), nullable=True),
        sa.Column('start_location_label', sa.String(length=200), nullable=True),
        sa.Column('similarity_signature', sa.String(length=40), nullable=False),
        sa.Column('profile_version', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['itinerary_id'], ['itineraries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('itinerary_id'),
    )
    op.create_index(
        'ix_itinerary_planning_profiles_destination_key', 'itinerary_planning_profiles', ['destination_key'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_itinerary_planning_profiles_destination_key', table_name='itinerary_planning_profiles')
    op.drop_table('itinerary_planning_profiles')
    op.drop_index('ix_itinerary_participants_itinerary_id', table_name='itinerary_participants')
    op.drop_table('itinerary_participants')

    with op.batch_alter_table('itinerary_items', schema=None) as batch_op:
        batch_op.drop_column('route_calculated_at')
        batch_op.drop_column('route_waypoint_key')
        batch_op.drop_column('route_geometry')
        batch_op.drop_column('route_source')
        batch_op.drop_column('route_status')

    with op.batch_alter_table('itineraries', schema=None) as batch_op:
        batch_op.drop_column('is_discoverable')
