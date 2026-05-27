from sqlmodel import SQLModel
from typing import Annotated
from fastapi import Depends

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings



engine = create_async_engine(
    url = settings.POSTGRESQL_URL,
    echo = True,
    connect_args={
        "statement_cache_size": 0
    }
)


async def create_db_tables():
    async with engine.begin() as connection:
        from .models import Organization, User
         
        # 1. DROP ALL TABLES (This wipes the database schema)
        # await connection.run_sync(SQLModel.metadata.drop_all)
        
        # 2. CREATE ALL TABLES (This rebuilds them with your new models)
        await connection.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


SessionDep = Annotated [AsyncSession, Depends(get_session)]