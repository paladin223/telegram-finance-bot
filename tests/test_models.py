"""
Тесты для SQLAlchemy моделей базы данных
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.database.models import User, Category, Transaction, Budget, Report
from app.database.schemas import TransactionType, ReportType


class TestUserModel:
    """Тесты для модели User"""
    
    def test_create_user(self, db_session):
        """Тест создания пользователя"""
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="ru"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.language_code == "ru"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_telegram_id_unique(self, db_session):
        """Тест уникальности telegram_id"""
        user1 = User(telegram_id=123456789, username="user1")
        user2 = User(telegram_id=123456789, username="user2")  # тот же ID
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_relationships(self, sample_user, sample_expense_category, sample_transaction):
        """Тест связей пользователя с другими объектами"""
        assert len(sample_user.categories) == 1
        assert sample_user.categories[0] == sample_expense_category
        assert len(sample_user.transactions) == 1
        assert sample_user.transactions[0] == sample_transaction


class TestCategoryModel:
    """Тесты для модели Category"""
    
    def test_create_category(self, db_session, sample_user):
        """Тест создания категории"""
        category = Category(
            name="Продукты",
            description="Продукты питания",
            user_id=sample_user.id,
            transaction_type=TransactionType.EXPENSE
        )
        
        db_session.add(category)
        db_session.commit()
        
        assert category.id is not None
        assert category.name == "Продукты"
        assert category.description == "Продукты питания"
        assert category.user_id == sample_user.id
        assert category.transaction_type == TransactionType.EXPENSE
        assert category.is_active is True
        assert category.created_at is not None

    def test_category_user_relationship(self, sample_expense_category, sample_user):
        """Тест связи категории с пользователем"""
        assert sample_expense_category.user == sample_user
        assert sample_expense_category in sample_user.categories

    def test_category_without_user_fails(self, db_session):
        """Тест что категория без пользователя не создается"""
        category = Category(
            name="Тест",
            transaction_type=TransactionType.EXPENSE,
            user_id=999  # несуществующий пользователь
        )
        
        db_session.add(category)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTransactionModel:
    """Тесты для модели Transaction"""
    
    def test_create_transaction(self, db_session, sample_user, sample_expense_category):
        """Тест создания транзакции"""
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
        
        assert transaction.id is not None
        assert transaction.amount == 1500.50
        assert transaction.description == "Покупка продуктов"
        assert transaction.transaction_type == TransactionType.EXPENSE
        assert transaction.user_id == sample_user.id
        assert transaction.category_id == sample_expense_category.id
        assert transaction.created_at is not None
        assert transaction.transaction_date == datetime(2024, 1, 15, 14, 30, 0)

    def test_transaction_relationships(self, sample_transaction, sample_user, sample_expense_category):
        """Тест связей транзакции"""
        assert sample_transaction.user == sample_user
        assert sample_transaction.category == sample_expense_category
        assert sample_transaction in sample_user.transactions
        assert sample_transaction in sample_expense_category.transactions

    def test_transaction_without_user_fails(self, db_session, sample_expense_category):
        """Тест что транзакция без пользователя не создается"""
        transaction = Transaction(
            amount=100.0,
            transaction_type=TransactionType.EXPENSE,
            user_id=999,  # несуществующий пользователь
            category_id=sample_expense_category.id
        )
        
        db_session.add(transaction)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_transaction_without_category_fails(self, db_session, sample_user):
        """Тест что транзакция без категории не создается"""
        transaction = Transaction(
            amount=100.0,
            transaction_type=TransactionType.EXPENSE,
            user_id=sample_user.id,
            category_id=999  # несуществующая категория
        )
        
        db_session.add(transaction)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestBudgetModel:
    """Тесты для модели Budget"""
    
    def test_create_budget(self, db_session, sample_user, sample_expense_category):
        """Тест создания бюджета"""
        budget = Budget(
            name="Месячный бюджет",
            amount=10000.00,
            spent_amount=3000.00,
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        db_session.add(budget)
        db_session.commit()
        
        assert budget.id is not None
        assert budget.name == "Месячный бюджет"
        assert budget.amount == 10000.00
        assert budget.spent_amount == 3000.00
        assert budget.user_id == sample_user.id
        assert budget.category_id == sample_expense_category.id
        assert budget.start_date == datetime(2024, 1, 1)
        assert budget.end_date == datetime(2024, 1, 31)
        assert budget.is_active is True
        assert budget.created_at is not None

    def test_budget_default_spent_amount(self, db_session, sample_user, sample_expense_category):
        """Тест значения по умолчанию для spent_amount"""
        budget = Budget(
            name="Тест",
            amount=5000.00,
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        db_session.add(budget)
        db_session.commit()
        
        assert budget.spent_amount == 0

    def test_budget_relationships(self, sample_budget, sample_user, sample_expense_category):
        """Тест связей бюджета"""
        assert sample_budget.user == sample_user
        assert sample_budget.category == sample_expense_category
        assert sample_budget in sample_user.budgets
        assert sample_budget in sample_expense_category.budgets


class TestReportModel:
    """Тесты для модели Report"""
    
    def test_create_report(self, db_session, sample_user):
        """Тест создания отчета"""
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
        
        assert report.id is not None
        assert report.name == "Месячный отчет"
        assert report.report_type == ReportType.MONTHLY
        assert report.user_id == sample_user.id
        assert report.start_date == datetime(2024, 1, 1)
        assert report.end_date == datetime(2024, 1, 31)
        assert report.data == '{"total_income": 50000, "total_expense": 30000}'
        assert report.created_at is not None

    def test_report_relationships(self, sample_report, sample_user):
        """Тест связей отчета"""
        assert sample_report.user == sample_user
        assert sample_report in sample_user.reports

    def test_report_without_user_fails(self, db_session):
        """Тест что отчет без пользователя не создается"""
        report = Report(
            name="Тест",
            report_type=ReportType.MONTHLY,
            user_id=999,  # несуществующий пользователь
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        db_session.add(report)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestCascadeDeletes:
    """Тесты каскадного удаления"""
    
    def test_user_deletion_cascades(self, db_session, sample_user, sample_expense_category, 
                                   sample_transaction, sample_budget, sample_report):
        """Тест что удаление пользователя удаляет все связанные объекты"""
        user_id = sample_user.id
        
        # Проверяем что объекты существуют
        assert db_session.get(User, user_id) is not None
        assert db_session.get(Category, sample_expense_category.id) is not None
        assert db_session.get(Transaction, sample_transaction.id) is not None
        assert db_session.get(Budget, sample_budget.id) is not None
        assert db_session.get(Report, sample_report.id) is not None
        
        # Удаляем пользователя
        db_session.delete(sample_user)
        db_session.commit()
        
        # Проверяем что все связанные объекты удалены
        assert db_session.get(User, user_id) is None
        assert db_session.get(Category, sample_expense_category.id) is None
        assert db_session.get(Transaction, sample_transaction.id) is None
        assert db_session.get(Budget, sample_budget.id) is None
        assert db_session.get(Report, sample_report.id) is None

    def test_category_deletion_cascades(self, db_session, sample_expense_category, 
                                       sample_transaction, sample_budget):
        """Тест что удаление категории удаляет связанные транзакции и бюджеты"""
        category_id = sample_expense_category.id
        transaction_id = sample_transaction.id
        budget_id = sample_budget.id
        
        # Удаляем категорию
        db_session.delete(sample_expense_category)
        db_session.commit()
        
        # Проверяем что связанные объекты удалены
        assert db_session.get(Category, category_id) is None
        assert db_session.get(Transaction, transaction_id) is None
        assert db_session.get(Budget, budget_id) is None 