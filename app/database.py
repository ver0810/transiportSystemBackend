from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


# MariaDB 连接 URL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1@localhost:3306/TRANSIPORT"

# 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)


def getSession():
    with Session(engine) as session:
        yield session
