"""
Модуль для работы с базой данных
"""

from typing import Generator, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_config
from .models import Base

# Создаем движок базы данных
engine: Optional[Engine] = None
session_factory: Optional[sessionmaker[Session]] = None


def init_database() -> None:
    """Инициализация базы данных"""
    global engine, session_factory
    
    config = get_config()
    
    # Преобразуем асинхронный URL в синхронный
    db_url: str = config.database_url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite:///")
    
    engine = create_engine(
        db_url,
        echo=config.debug,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    session_factory = sessionmaker(bind=engine)
    
    # Создаем таблицы
    Base.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Получение сессии базы данных"""
    if session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()


def close_database() -> None:
    """Закрытие соединения с базой данных"""
    global engine
    if engine:
        engine.dispose() 