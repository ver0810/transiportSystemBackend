from os import name
from venv import create
from weakref import ref
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):

    __tablename__ = "users"  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(min_length=3, max_length=20)
    hashedPassword: str

class RoadNetwork(SQLModel, table=True):
    __tablename__ = "roads"  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    geometry: str  # WKT 格式
    created_at: str