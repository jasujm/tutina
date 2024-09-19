from enum import Enum

from sqlalchemy import (
    URL,
    Boolean,
    Column,
    Connection,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    func,
    select,
)
from sqlalchemy import (
    Enum as EnumField,
)

from .settings import settings

engine = create_engine(settings.get_database_url())

metadata = MetaData()


class HvacState(Enum):
    off = "off"
    auto = "auto"
    cool = "cool"
    heat = "heat"
    dry = "dry"
    fan_only = "fan_only"


class OpeningType(Enum):
    door = "door"
    window = "window"


UTC_NOW = func.convert_tz(func.now(), "SYSTEM", "+00:00")


locations = Table(
    "locations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("slug", String(31), nullable=False, unique=True),
)


measurements = Table(
    "measurements",
    metadata,
    Column("timestamp", DateTime, default=UTC_NOW, primary_key=True),
    Column("location_id", Integer, ForeignKey("locations.id"), primary_key=True),
    Column("temperature", Float),
    Column("humidity", Float),
    Column("pressure", Float),
)

forecasts = Table(
    "forecasts",
    metadata,
    Column("timestamp", DateTime, default=UTC_NOW, primary_key=True),
    Column("reference_timestamp", DateTime, primary_key=True),
    Column("temperature", Float, nullable=False),
    Column("humidity", Float, nullable=False),
    Column("pressure", Float, nullable=False),
    Column("wind_speed", Float, nullable=False),
    Column("status", String(31), nullable=False),
)

hvac_devices = Table(
    "hvac_devices",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("slug", String(31), nullable=False, unique=True),
)

hvacs = Table(
    "hvacs",
    metadata,
    Column("timestamp", DateTime, default=UTC_NOW, primary_key=True),
    Column("device_id", Integer, ForeignKey("hvac_devices.id"), primary_key=True),
    Column("state", EnumField(HvacState), nullable=True),
    Column("temperature", Float, nullable=True),
)

openings = Table(
    "openings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type", EnumField(OpeningType), nullable=False),
    Column("slug", String(31), nullable=False),
    UniqueConstraint("type", "slug"),
)

opening_states = Table(
    "opening_states",
    metadata,
    Column("timestamp", DateTime, default=UTC_NOW, primary_key=True),
    Column("opening_id", Integer, ForeignKey("openings.id"), primary_key=True),
    Column("is_open", Boolean, nullable=False),
)

metadata.create_all(engine)
