from fastapi import Depends
from sqlmodel import SQLModel, Field, create_engine, Session, Relationship
from typing import Annotated
from .settings import DATABASE_URL

conn_str = str(DATABASE_URL)
engine = create_engine(conn_str)


def get_db():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


db_type = Annotated[Session, Depends(get_db)]


class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    hashed_password: str
    todos: list["Todos"] = Relationship(back_populates="user")


class Todos(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: Users = Relationship(back_populates="todos")
    description: str
    email: str | None = Field(default=None, foreign_key="users.email")
    completed: bool
