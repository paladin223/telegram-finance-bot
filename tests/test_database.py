"""
Тесты для настройки и подключения к базе данных
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import init_database, get_session, close_database


class TestDatabaseInitialization:
    """Тесты инициализации базы данных"""
    
    @patch('app.database.database.get_config')
    @patch('app.database.database.create_engine')
    @patch('app.database.database.sessionmaker')
    @patch('app.database.database.Base.metadata.create_all')
    def test_init_database_postgresql_asyncpg_url(self, mock_create_all, mock_sessionmaker, 
                                                  mock_create_engine, mock_get_config):
        """Тест инициализации с PostgreSQL asyncpg URL"""
        mock_config = MagicMock()
        mock_config.database_url = "postgresql+asyncpg://user:pass@localhost/db"
        mock_config.debug = False
        mock_get_config.return_value = mock_config
        
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        init_database()
        
        # Проверяем что asyncpg URL преобразован в psycopg2
        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost/db",
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

    @patch('app.database.database.get_config')
    @patch('app.database.database.create_engine')
    @patch('app.database.database.sessionmaker')
    @patch('app.database.database.Base.metadata.create_all')
    def test_init_database_postgresql_regular_url(self, mock_create_all, mock_sessionmaker, 
                                                  mock_create_engine, mock_get_config):
        """Тест инициализации с обычным PostgreSQL URL"""
        mock_config = MagicMock()
        mock_config.database_url = "postgresql://user:pass@localhost/db"
        mock_config.debug = True
        mock_get_config.return_value = mock_config
        
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        init_database()
        
        # URL не должен измениться
        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost/db",
            echo=True,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

    def test_get_session_not_initialized(self):
        """Тест получения сессии без инициализации"""
        import app.database.database as db_module
        original_factory = db_module.session_factory
        db_module.session_factory = None
        
        try:
            with pytest.raises(RuntimeError, match="Database not initialized"):
                session_generator = get_session()
                next(session_generator)
        finally:
            db_module.session_factory = original_factory

    def test_close_database_without_engine(self):
        """Тест закрытия базы данных когда engine отсутствует"""
        import app.database.database as db_module
        original_engine = db_module.engine
        db_module.engine = None
        
        try:
            # Должно выполниться без ошибок
            close_database()
        finally:
            db_module.engine = original_engine


class TestDatabaseIntegration:
    """Интеграционные тесты базы данных с реальным PostgreSQL"""
    
    @pytest.mark.database
    def test_database_connection(self, db_session):
        """Тест подключения к базе данных"""
        # Выполняем простой запрос
        result = db_session.execute(text("SELECT 1 as test_value")).scalar()
        assert result == 1

    @pytest.mark.database
    def test_database_tables_exist(self, db_session):
        """Тест что все таблицы созданы"""
        # Проверяем что основные таблицы существуют
        tables = [
            'users', 'categories', 'transactions', 
            'budgets', 'reports'
        ]
        
        for table_name in tables:
            result = db_session.execute(
                text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
            ).scalar()
            assert result is True, f"Таблица {table_name} не существует"

    @pytest.mark.database
    def test_session_isolation(self, engine):
        """Тест изоляции сессий"""
        from sqlalchemy.orm import sessionmaker
        
        SessionLocal = sessionmaker(bind=engine)
        
        # Создаем две сессии
        session1 = SessionLocal()
        session2 = SessionLocal()
        
        try:
            # Проверяем что это разные объекты
            assert session1 is not session2
            
            # Проверяем что обе сессии работают
            result1 = session1.execute(text("SELECT 1")).scalar()
            result2 = session2.execute(text("SELECT 2")).scalar()
            
            assert result1 == 1
            assert result2 == 2
        finally:
            session1.close()
            session2.close()

    @pytest.mark.database
    def test_transaction_rollback(self, db_session, sample_user):
        """Тест отката транзакций"""
        from app.database.models import User
        
        initial_count = db_session.query(User).count()
        
        # Используем nested transaction вместо begin()
        savepoint = db_session.begin_nested()
        
        try:
            # Добавляем нового пользователя
            new_user = User(
                telegram_id=999999999,
                username="test_rollback"
            )
            db_session.add(new_user)
            db_session.flush()  # Отправляем в БД но не коммитим
            
            # Проверяем что пользователь добавлен в сессии
            count_in_transaction = db_session.query(User).count()
            assert count_in_transaction == initial_count + 1
            
            # Откатываем
            savepoint.rollback()
            
            # Проверяем что изменения отменены
            final_count = db_session.query(User).count()
            assert final_count == initial_count
            
        except Exception:
            savepoint.rollback()
            raise 