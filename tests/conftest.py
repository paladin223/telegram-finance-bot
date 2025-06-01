"""
Конфигурация pytest и общие фикстуры для тестирования базы данных
"""

import pytest
import os
import random
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.database.models import Base, User, Category, Transaction, Budget, Report
from app.database.schemas import TransactionType, ReportType


# PostgreSQL настройки для тестов
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/test_finance_bot"
)


@pytest.fixture(scope="session")
def engine():
    """Движок базы данных для тестов (PostgreSQL)"""
    engine = create_engine(
        TEST_DATABASE_URL, 
        echo=False,
        pool_pre_ping=True
    )
    
    # Создаем таблицы
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Очищаем после всех тестов
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """Сессия базы данных для каждого теста"""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Очищаем все таблицы перед каждым тестом
    session.execute(text("TRUNCATE TABLE transactions, budgets, reports, categories, users RESTART IDENTITY CASCADE"))
    session.commit()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_user(db_session) -> User:
    """Создает тестового пользователя в БД"""
    telegram_id = random.randint(100000000, 999999999)
    
    user = User(
        telegram_id=telegram_id,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="ru"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_expense_category(db_session, sample_user) -> Category:
    """Создает тестовую категорию расходов в БД"""
    category = Category(
        name="Продукты",
        description="Продукты питания",
        user_id=sample_user.id,
        transaction_type=TransactionType.EXPENSE
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_income_category(db_session, sample_user) -> Category:
    """Создает тестовую категорию доходов в БД"""
    category = Category(
        name="Зарплата",
        description="Основная зарплата",
        user_id=sample_user.id,
        transaction_type=TransactionType.INCOME
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_transaction(db_session, sample_user, sample_expense_category) -> Transaction:
    """Создает тестовую транзакцию в БД"""
    transaction = Transaction(
        amount=1500.50,
        description="Покупка продуктов",
        transaction_type=TransactionType.EXPENSE,
        user_id=sample_user.id,
        category_id=sample_expense_category.id,
        transaction_date=datetime(2024, 1, 15, 14, 30, 0)
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction


@pytest.fixture
def sample_budget(db_session, sample_user, sample_expense_category) -> Budget:
    """Создает тестовый бюджет в БД"""
    budget = Budget(
        name="Бюджет на продукты",
        amount=10000.00,
        spent_amount=3000.00,
        user_id=sample_user.id,
        category_id=sample_expense_category.id,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    return budget


@pytest.fixture
def sample_report(db_session, sample_user) -> Report:
    """Создает тестовый отчет в БД"""
    report = Report(
        name="Месячный отчет",
        report_type=ReportType.MONTHLY,
        user_id=sample_user.id,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        data='{"total_income": 50000, "total_expense": 30000}'
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report 