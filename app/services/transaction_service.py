"""
Сервис для работы с транзакциями
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.database.schemas import Transaction, TransactionType
from app.database.queries import TransactionQueries, UserQueries, CategoryQueries


class TransactionService:
    """Сервис для работы с транзакциями"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add_transaction(
        self,
        telegram_id: int,
        amount: Decimal,
        category_name: str,
        transaction_type: TransactionType,
        description: Optional[str] = None,
        transaction_date: Optional[datetime] = None
    ) -> Transaction:
        """Добавление новой транзакции"""
        
        # Получаем пользователя
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            # Автоматически создаем пользователя если его нет
            user = UserQueries.create_user(
                self.session,
                telegram_id=telegram_id,
                username=f"user_{telegram_id}",
                first_name="Пользователь"
            )
        
        # Получаем или создаем категорию
        categories = CategoryQueries.get_user_categories(
            self.session, user.id, transaction_type
        )
        
        category = None
        for cat in categories:
            if cat.name.lower() == category_name.lower():
                category = cat
                break
        
        if not category:
            # Создаем новую категорию
            category = CategoryQueries.create_category(
                self.session, category_name, user.id, transaction_type
            )
        
        # Создаем транзакцию
        transaction = TransactionQueries.create_transaction(
            self.session,
            amount=amount,
            user_id=user.id,
            category_id=category.id,
            transaction_type=transaction_type,
            description=description,
            transaction_date=transaction_date
        )
        
        return transaction
    
    def get_user_transactions(
        self,
        telegram_id: int,
        limit: int = 10,
        transaction_type: Optional[TransactionType] = None,
        category_name: Optional[str] = None
    ) -> List[Transaction]:
        """Получение транзакций пользователя"""
        
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            return []
        
        category_id = None
        if category_name:
            categories = CategoryQueries.get_user_categories(self.session, user.id)
            for cat in categories:
                if cat.name.lower() == category_name.lower():
                    category_id = cat.id
                    break
        
        transactions = TransactionQueries.get_user_transactions(
            self.session,
            user_id=user.id,
            limit=limit,
            transaction_type=transaction_type,
            category_id=category_id
        )
        
        return transactions
    
    def get_monthly_statistics(
        self,
        telegram_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Получение месячной статистики"""
        
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            # Автоматически создаем пользователя если его нет
            user = UserQueries.create_user(
                self.session,
                telegram_id=telegram_id,
                username=f"user_{telegram_id}",
                first_name="Пользователь"
            )
        
        now = datetime.utcnow()
        target_year = year or now.year
        target_month = month or now.month
        
        # Получаем сводку по доходам и расходам
        start_date = datetime(target_year, target_month, 1)
        if target_month == 12:
            end_date = datetime(target_year + 1, 1, 1)
        else:
            end_date = datetime(target_year, target_month + 1, 1)
        
        # Доходы по категориям
        income_by_category = TransactionQueries.get_transactions_sum_by_category(
            self.session, user.id, start_date, end_date, TransactionType.INCOME
        )
        
        # Расходы по категориям
        expense_by_category = TransactionQueries.get_transactions_sum_by_category(
            self.session, user.id, start_date, end_date, TransactionType.EXPENSE
        )
        
        total_income = sum(item['total_amount'] for item in income_by_category)
        total_expense = sum(item['total_amount'] for item in expense_by_category)
        
        return {
            'period': f"{target_year}-{target_month:02d}",
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': total_income - total_expense,
            'income_by_category': income_by_category,
            'expense_by_category': expense_by_category
        }
    
    def format_transaction_message(self, transaction: Transaction) -> str:
        """Форматирование сообщения о транзакции"""
        type_emoji = "💰" if transaction.transaction_type == TransactionType.INCOME else "💸"
        
        message = (
            f"{type_emoji} <b>{transaction.transaction_type.value.title()}</b>\n"
            f"💵 Сумма: {transaction.amount} руб.\n"
            f"📂 Категория: {transaction.category.name if transaction.category else 'Без категории'}\n"
            f"📅 Дата: {transaction.transaction_date.strftime('%d.%m.%Y %H:%M')}\n"
        )
        
        if transaction.description:
            message += f"📝 Описание: {transaction.description}\n"
        
        return message 