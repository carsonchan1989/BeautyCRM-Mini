"""Update Service and ServiceItem models to match Excel processing logic

Revision ID: bf691175e2fa
Revises: 
Create Date: 2025-04-02 14:14:10.957098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf691175e2fa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('customers',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('gender', sa.String(length=8), nullable=True),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('store', sa.String(length=64), nullable=True),
    sa.Column('hometown', sa.String(length=128), nullable=True),
    sa.Column('residence', sa.String(length=256), nullable=True),
    sa.Column('residence_years', sa.String(length=32), nullable=True),
    sa.Column('family_structure', sa.String(length=256), nullable=True),
    sa.Column('family_age_distribution', sa.String(length=256), nullable=True),
    sa.Column('living_condition', sa.String(length=256), nullable=True),
    sa.Column('personality_tags', sa.String(length=256), nullable=True),
    sa.Column('consumption_decision', sa.String(length=64), nullable=True),
    sa.Column('risk_sensitivity', sa.String(length=64), nullable=True),
    sa.Column('hobbies', sa.String(length=256), nullable=True),
    sa.Column('routine', sa.String(length=256), nullable=True),
    sa.Column('diet_preference', sa.String(length=256), nullable=True),
    sa.Column('menstrual_record', sa.Text(), nullable=True),
    sa.Column('family_medical_history', sa.Text(), nullable=True),
    sa.Column('occupation', sa.String(length=64), nullable=True),
    sa.Column('work_unit_type', sa.String(length=64), nullable=True),
    sa.Column('annual_income', sa.String(length=32), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('projects',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('category', sa.String(length=64), nullable=True),
    sa.Column('effects', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('sessions', sa.Integer(), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('materials', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=16), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('communications',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.String(length=32), nullable=False),
    sa.Column('communication_date', sa.DateTime(), nullable=False),
    sa.Column('communication_type', sa.String(length=32), nullable=True),
    sa.Column('communication_location', sa.String(length=64), nullable=True),
    sa.Column('staff_name', sa.String(length=64), nullable=True),
    sa.Column('communication_content', sa.Text(), nullable=True),
    sa.Column('customer_feedback', sa.Text(), nullable=True),
    sa.Column('follow_up_action', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('consumptions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.String(length=32), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('project_name', sa.String(length=128), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('payment_method', sa.String(length=32), nullable=True),
    sa.Column('total_sessions', sa.Integer(), nullable=True),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.Column('satisfaction', sa.String(length=32), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('health_records',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.String(length=32), nullable=False),
    sa.Column('skin_type', sa.String(length=32), nullable=True),
    sa.Column('oil_water_balance', sa.String(length=128), nullable=True),
    sa.Column('pores_blackheads', sa.String(length=128), nullable=True),
    sa.Column('wrinkles_texture', sa.String(length=128), nullable=True),
    sa.Column('pigmentation', sa.String(length=128), nullable=True),
    sa.Column('photoaging_inflammation', sa.String(length=128), nullable=True),
    sa.Column('tcm_constitution', sa.String(length=64), nullable=True),
    sa.Column('tongue_features', sa.String(length=64), nullable=True),
    sa.Column('pulse_data', sa.String(length=64), nullable=True),
    sa.Column('sleep_routine', sa.String(length=128), nullable=True),
    sa.Column('exercise_pattern', sa.String(length=128), nullable=True),
    sa.Column('diet_restrictions', sa.String(length=128), nullable=True),
    sa.Column('care_time_flexibility', sa.String(length=64), nullable=True),
    sa.Column('massage_pressure_preference', sa.String(length=64), nullable=True),
    sa.Column('environment_requirements', sa.String(length=256), nullable=True),
    sa.Column('short_term_beauty_goal', sa.String(length=256), nullable=True),
    sa.Column('long_term_beauty_goal', sa.String(length=256), nullable=True),
    sa.Column('short_term_health_goal', sa.String(length=256), nullable=True),
    sa.Column('long_term_health_goal', sa.String(length=256), nullable=True),
    sa.Column('medical_cosmetic_history', sa.Text(), nullable=True),
    sa.Column('wellness_service_history', sa.Text(), nullable=True),
    sa.Column('major_disease_history', sa.Text(), nullable=True),
    sa.Column('allergies', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('services',
    sa.Column('service_id', sa.String(length=50), nullable=False),
    sa.Column('customer_id', sa.String(length=32), nullable=False),
    sa.Column('customer_name', sa.String(length=64), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('service_date', sa.DateTime(), nullable=False),
    sa.Column('departure_time', sa.DateTime(), nullable=True),
    sa.Column('total_amount', sa.Float(), nullable=True),
    sa.Column('total_sessions', sa.Integer(), nullable=True),
    sa.Column('payment_method', sa.String(length=32), nullable=True),
    sa.Column('operator', sa.String(length=64), nullable=True),
    sa.Column('remark', sa.Text(), nullable=True),
    sa.Column('satisfaction', sa.String(length=32), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('service_id')
    )
    op.create_table('service_items',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('service_id', sa.String(length=50), nullable=False),
    sa.Column('project_id', sa.String(length=50), nullable=True),
    sa.Column('project_name', sa.String(length=128), nullable=False),
    sa.Column('beautician_name', sa.String(length=64), nullable=True),
    sa.Column('unit_price', sa.Float(), nullable=True),
    sa.Column('card_deduction', sa.Float(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('is_specified', sa.Boolean(), nullable=True),
    sa.Column('remark', sa.Text(), nullable=True),
    sa.Column('is_satisfied', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['service_id'], ['services.service_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('service_items')
    op.drop_table('services')
    op.drop_table('health_records')
    op.drop_table('consumptions')
    op.drop_table('communications')
    op.drop_table('projects')
    op.drop_table('customers')
    # ### end Alembic commands ###
