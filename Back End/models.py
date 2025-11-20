from sqlalchemy import (
    Table, Column, Integer, String, MetaData, create_engine, Text
)
from sqlalchemy.sql import select

DB_URL = "sqlite:///reports.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = MetaData()

reports = Table(
    "reports",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hash", String, nullable=False),
    Column("description", Text, nullable=False),
    Column("category", String, nullable=False),
    Column("location", String, nullable=True),
    Column("user", String, nullable=False),
    Column("ai_response", Text, nullable=True),
    Column("tx_hash", String, nullable=True),
    Column("created_at", String, nullable=False)
)

metadata.create_all(engine)
