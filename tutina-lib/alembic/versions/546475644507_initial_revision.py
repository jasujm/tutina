"""Initial revision

Revision ID: 546475644507
Revises:
Create Date: 2025-02-02 13:29:10.294959

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "546475644507"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forecasts",
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("reference_timestamp", sa.DateTime(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("humidity", sa.Float(), nullable=False),
        sa.Column("pressure", sa.Float(), nullable=False),
        sa.Column("wind_speed", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=31), nullable=False),
        sa.PrimaryKeyConstraint("timestamp", "reference_timestamp"),
    )
    op.create_table(
        "hvac_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=31), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=31), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "openings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "type", sa.Enum("door", "window", name="openingtype"), nullable=False
        ),
        sa.Column("slug", sa.String(length=31), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type", "slug"),
    )
    op.create_table(
        "hvacs",
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column(
            "state",
            sa.Enum("off", "auto", "cool", "heat", "dry", "fan_only", name="hvacstate"),
            nullable=True,
        ),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["hvac_devices.id"],
        ),
        sa.PrimaryKeyConstraint("timestamp", "device_id"),
    )
    op.create_table(
        "measurements",
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        sa.Column("pressure", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
        ),
        sa.PrimaryKeyConstraint("timestamp", "location_id"),
    )
    op.create_table(
        "opening_states",
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("opening_id", sa.Integer(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["opening_id"],
            ["openings.id"],
        ),
        sa.PrimaryKeyConstraint("timestamp", "opening_id"),
    )


def downgrade() -> None:
    op.drop_table("opening_states")
    op.drop_table("measurements")
    op.drop_table("hvacs")
    op.drop_table("openings")
    op.drop_table("locations")
    op.drop_table("hvac_devices")
    op.drop_table("forecasts")
