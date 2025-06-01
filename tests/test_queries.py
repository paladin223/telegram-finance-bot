"""
Тесты для запросов к базе данных
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.database.queries import (
    UserQueries, CategoryQueries, TransactionQueries, 
    BudgetQueries, ReportQueries, AnalyticsQueries
)
from app.database.schemas import TransactionType, ReportType


class TestUserQueries:
    """Тесты для UserQueries"""
    
    def test_create_user(self, db_session):
        """Тест создания пользователя через запрос"""
        user = UserQueries.create_user(
            db_session,
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="ru"
        )
        
        assert user.id is not None
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.language_code == "ru"

    def test_get_user_by_telegram_id_existing(self, db_session, sample_user):
        """Тест получения существующего пользователя по telegram_id"""
        user = UserQueries.get_user_by_telegram_id(db_session, sample_user.telegram_id)
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.telegram_id == sample_user.telegram_id

    def test_get_user_by_telegram_id_not_found(self, db_session):
        """Тест получения несуществующего пользователя"""
        user = UserQueries.get_user_by_telegram_id(db_session, 999999999)
        
        assert user is None

    def test_get_user_with_relations(self, db_session, sample_user, sample_expense_category, sample_transaction):
        """Тест получения пользователя со связанными данными"""
        user = UserQueries.get_user_with_relations(db_session, sample_user.id)
        
        assert user is not None
        assert len(user.categories) == 1
        assert len(user.transactions) == 1
        assert user.categories[0].name == "Продукты"
        assert user.transactions[0].amount == 1500.50


class TestCategoryQueries:
    """Тесты для CategoryQueries"""
    
    def test_create_category(self, db_session, sample_user):
        """Тест создания категории через запрос"""
        category = CategoryQueries.create_category(
            db_session,
            name="Транспорт",
            user_id=sample_user.id,
            transaction_type=TransactionType.EXPENSE,
            description="Транспортные расходы"
        )
        
        assert category.id is not None
        assert category.name == "Транспорт"
        assert category.description == "Транспортные расходы"
        assert category.user_id == sample_user.id
        assert category.transaction_type == TransactionType.EXPENSE

    def test_get_user_categories_all(self, db_session, sample_user, sample_expense_category, sample_income_category):
        """Тест получения всех категорий пользователя"""
        categories = CategoryQueries.get_user_categories(db_session, sample_user.id)
        
        assert len(categories) == 2
        category_names = [cat.name for cat in categories]
        assert "Продукты" in category_names
        assert "Зарплата" in category_names

    def test_get_user_categories_by_type(self, db_session, sample_user, sample_expense_category, sample_income_category):
        """Тест получения категорий по типу"""
        expense_categories = CategoryQueries.get_user_categories(
            db_session, sample_user.id, TransactionType.EXPENSE
        )
        income_categories = CategoryQueries.get_user_categories(
            db_session, sample_user.id, TransactionType.INCOME
        )
        
        assert len(expense_categories) == 1
        assert expense_categories[0].name == "Продукты"
        assert len(income_categories) == 1
        assert income_categories[0].name == "Зарплата"

    def test_get_user_categories_empty(self, db_session, sample_user):
        """Тест получения категорий для пользователя без категорий"""
        # Удаляем все категории
        for category in sample_user.categories:
            db_session.delete(category)
        db_session.commit()
        
        categories = CategoryQueries.get_user_categories(db_session, sample_user.id)
        assert len(categories) == 0


class TestTransactionQueries:
    """Тесты для TransactionQueries"""
    
    def test_create_transaction(self, db_session, sample_user, sample_expense_category):
        """Тест создания транзакции через запрос"""
        transaction_date = datetime(2024, 2, 1, 10, 0, 0)
        transaction = TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("500.00"),
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            transaction_type=TransactionType.EXPENSE,
            description="Кофе",
            transaction_date=transaction_date
        )
        
        assert transaction.id is not None
        assert transaction.amount == 500.00
        assert transaction.description == "Кофе"
        assert transaction.transaction_type == TransactionType.EXPENSE
        assert transaction.transaction_date == transaction_date

    def test_get_user_transactions_all(self, db_session, sample_user, sample_transaction):
        """Тест получения всех транзакций пользователя"""
        transactions = TransactionQueries.get_user_transactions(db_session, sample_user.id)
        
        assert len(transactions) == 1
        assert transactions[0].id == sample_transaction.id

    def test_get_user_transactions_with_limit(self, db_session, sample_user, sample_expense_category):
        """Тест получения транзакций с лимитом"""
        # Создаем несколько транзакций
        for i in range(5):
            TransactionQueries.create_transaction(
                db_session,
                amount=Decimal(f"{100 + i}.00"),
                user_id=sample_user.id,
                category_id=sample_expense_category.id,
                transaction_type=TransactionType.EXPENSE
            )
        
        transactions = TransactionQueries.get_user_transactions(db_session, sample_user.id, limit=3)
        assert len(transactions) == 3

    def test_get_user_transactions_by_type(self, db_session, sample_user, sample_expense_category, sample_income_category):
        """Тест получения транзакций по типу"""
        # Сначала проверим количество существующих транзакций
        existing_expense_count = len(TransactionQueries.get_user_transactions(
            db_session, sample_user.id, transaction_type=TransactionType.EXPENSE
        ))
        existing_income_count = len(TransactionQueries.get_user_transactions(
            db_session, sample_user.id, transaction_type=TransactionType.INCOME
        ))
        
        # Создаем транзакции разных типов
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("200.00"),
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            transaction_type=TransactionType.EXPENSE
        )
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("5000.00"),
            user_id=sample_user.id,
            category_id=sample_income_category.id,
            transaction_type=TransactionType.INCOME
        )
        
        expense_transactions = TransactionQueries.get_user_transactions(
            db_session, sample_user.id, transaction_type=TransactionType.EXPENSE
        )
        income_transactions = TransactionQueries.get_user_transactions(
            db_session, sample_user.id, transaction_type=TransactionType.INCOME
        )
        
        assert len(expense_transactions) == existing_expense_count + 1
        assert len(income_transactions) == existing_income_count + 1

    def test_get_user_transactions_by_date_range(self, db_session, sample_user, sample_expense_category):
        """Тест получения транзакций по диапазону дат"""
        # Проверяем сколько транзакций уже есть в 2024 году
        existing_2024_count = len(TransactionQueries.get_user_transactions(
            db_session,
            sample_user.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        ))
        
        # Создаем транзакции с разными датами
        old_date = datetime(2023, 12, 1)
        new_date = datetime(2024, 2, 1)
        
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("100.00"),
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            transaction_type=TransactionType.EXPENSE,
            transaction_date=old_date
        )
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("200.00"),
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            transaction_type=TransactionType.EXPENSE,
            transaction_date=new_date
        )
        
        # Получаем только за 2024 год
        transactions = TransactionQueries.get_user_transactions(
            db_session,
            sample_user.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        
        assert len(transactions) == existing_2024_count + 1  # только new_date попадает в 2024

    def test_get_transactions_sum_by_category(self, db_session, sample_user, sample_expense_category):
        """Тест получения суммы транзакций по категориям"""
        # Проверяем существующую сумму в январе 2024
        existing_result = TransactionQueries.get_transactions_sum_by_category(
            db_session, sample_user.id, datetime(2024, 1, 1), datetime(2024, 1, 31), TransactionType.EXPENSE
        )
        existing_amount = existing_result[0]['total_amount'] if existing_result else Decimal('0')
        existing_count = existing_result[0]['transaction_count'] if existing_result else 0
        
        # Создаем несколько транзакций
        new_amounts = []
        for amount in [100, 200, 300]:
            new_amounts.append(Decimal(str(amount)))
            TransactionQueries.create_transaction(
                db_session,
                amount=Decimal(str(amount)),
                user_id=sample_user.id,
                category_id=sample_expense_category.id,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=datetime(2024, 1, 15)
            )
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = TransactionQueries.get_transactions_sum_by_category(
            db_session, sample_user.id, start_date, end_date, TransactionType.EXPENSE
        )
        
        assert len(result) == 1
        assert result[0]['category_name'] == "Продукты"
        expected_amount = existing_amount + sum(new_amounts)
        assert result[0]['total_amount'] == expected_amount
        assert result[0]['transaction_count'] == existing_count + 3


class TestBudgetQueries:
    """Тесты для BudgetQueries"""
    
    def test_create_budget(self, db_session, sample_user, sample_expense_category):
        """Тест создания бюджета через запрос"""
        budget = BudgetQueries.create_budget(
            db_session,
            name="Недельный бюджет",
            amount=Decimal("2000.00"),
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 7)
        )
        
        assert budget.id is not None
        assert budget.name == "Недельный бюджет"
        assert budget.amount == 2000.00
        assert budget.spent_amount == 0


class TestReportQueries:
    """Тесты для ReportQueries"""
    
    def test_create_report(self, db_session, sample_user):
        """Тест создания отчета через запрос"""
        report = ReportQueries.create_report(
            db_session,
            name="Недельный отчет",
            user_id=sample_user.id,
            report_type=ReportType.WEEKLY,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 7),
            data='{"income": 1000, "expense": 500}'
        )
        
        assert report.id is not None
        assert report.name == "Недельный отчет"
        assert report.report_type == ReportType.WEEKLY
        assert report.data == '{"income": 1000, "expense": 500}'

    def test_get_user_reports(self, db_session, sample_user, sample_report):
        """Тест получения отчетов пользователя"""
        reports = ReportQueries.get_user_reports(db_session, sample_user.id)
        
        assert len(reports) == 1
        assert reports[0].id == sample_report.id

    def test_get_user_reports_by_type(self, db_session, sample_user):
        """Тест получения отчетов по типу"""
        # Проверяем существующие отчеты
        existing_monthly_count = len(ReportQueries.get_user_reports(
            db_session, sample_user.id, ReportType.MONTHLY
        ))
        existing_weekly_count = len(ReportQueries.get_user_reports(
            db_session, sample_user.id, ReportType.WEEKLY
        ))
        
        # Создаем отчеты разных типов
        ReportQueries.create_report(
            db_session,
            name="Месячный отчет",
            user_id=sample_user.id,
            report_type=ReportType.MONTHLY,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            data='{}'
        )
        ReportQueries.create_report(
            db_session,
            name="Недельный отчет",
            user_id=sample_user.id,
            report_type=ReportType.WEEKLY,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 7),
            data='{}'
        )
        
        monthly_reports = ReportQueries.get_user_reports(
            db_session, sample_user.id, ReportType.MONTHLY
        )
        weekly_reports = ReportQueries.get_user_reports(
            db_session, sample_user.id, ReportType.WEEKLY
        )
        
        assert len(monthly_reports) == existing_monthly_count + 1
        assert len(weekly_reports) == existing_weekly_count + 1


class TestAnalyticsQueries:
    """Тесты для AnalyticsQueries"""
    
    def test_get_monthly_summary(self, db_session, sample_user, sample_expense_category, sample_income_category):
        """Тест получения месячной сводки"""
        # Создаем транзакции за январь 2024
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("50000.00"),
            user_id=sample_user.id,
            category_id=sample_income_category.id,
            transaction_type=TransactionType.INCOME,
            transaction_date=datetime(2024, 1, 5)
        )
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("2000.00"),
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            transaction_type=TransactionType.EXPENSE,
            transaction_date=datetime(2024, 1, 10)
        )
        
        summary = AnalyticsQueries.get_monthly_summary(db_session, sample_user.id, 2024, 1)
        
        # Проверяем основную структуру ответа
        assert 'year' in summary
        assert 'month' in summary
        assert 'total_income' in summary
        assert 'total_expenses' in summary  # с 's'!
        assert 'balance' in summary
        assert 'top_expense_categories' in summary
        
        assert summary['year'] == 2024
        assert summary['month'] == 1
        assert summary['total_income'] == Decimal('50000.00')
        # Проверяем что расходы включают существующие транзакции
        assert summary['total_expenses'] >= Decimal('2000.00')
        assert summary['balance'] == summary['total_income'] - summary['total_expenses']

    def test_get_top_expense_categories(self, db_session, sample_user, sample_expense_category):
        """Тест получения топ категорий расходов"""
        # Создаем дополнительную категорию
        transport_category = CategoryQueries.create_category(
            db_session,
            name="Транспорт",
            user_id=sample_user.id,
            transaction_type=TransactionType.EXPENSE
        )
        
        # Получаем текущую сумму по категории "Продукты" за январь 2024
        existing_food_sum = Decimal('0')
        existing_result = TransactionQueries.get_transactions_sum_by_category(
            db_session, sample_user.id, datetime(2024, 1, 1), datetime(2024, 1, 31), TransactionType.EXPENSE
        )
        for item in existing_result:
            if item['category_name'] == "Продукты":
                existing_food_sum = item['total_amount']
                break
        
        # Создаем транзакции
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("3000.00"),
            user_id=sample_user.id,
            category_id=transport_category.id,
            transaction_type=TransactionType.EXPENSE,
            transaction_date=datetime(2024, 1, 10)
        )
        TransactionQueries.create_transaction(
            db_session,
            amount=Decimal("500.00"),
            user_id=sample_user.id,
            category_id=sample_expense_category.id,
            transaction_type=TransactionType.EXPENSE,
            transaction_date=datetime(2024, 1, 15)
        )
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        top_categories = AnalyticsQueries.get_top_expense_categories(
            db_session, sample_user.id, start_date, end_date, limit=5
        )
        
        assert len(top_categories) == 2
        # Транспорт должен быть первым (3000 > existing_food_sum + 500)
        assert top_categories[0]['category_name'] == "Транспорт"
        assert top_categories[0]['total_amount'] == Decimal('3000.00')
        assert top_categories[1]['category_name'] == "Продукты"
        expected_food_total = existing_food_sum + Decimal('500.00')
        assert top_categories[1]['total_amount'] == expected_food_total 