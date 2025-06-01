"""
Сервис для работы с бюджетами
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.database.schemas import Budget, TransactionType
from app.database.queries import BudgetQueries, UserQueries, CategoryQueries


class BudgetService:
    """Сервис для работы с бюджетами"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_budget(
        self,
        telegram_id: int,
        name: str,
        amount: Decimal,
        category_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> Budget:
        """Создание нового бюджета"""
        
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
        
        # Получаем или создаем категорию расходов
        categories = CategoryQueries.get_user_categories(
            self.session, user.id, TransactionType.EXPENSE
        )
        
        category = None
        for cat in categories:
            if cat.name.lower() == category_name.lower():
                category = cat
                break
        
        if not category:
            # Создаем новую категорию расходов
            category = CategoryQueries.create_category(
                self.session, category_name, user.id, TransactionType.EXPENSE
            )
        
        # Создаем бюджет
        budget = BudgetQueries.create_budget(
            self.session,
            name=name,
            amount=amount,
            user_id=user.id,
            category_id=category.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return budget
    
    def get_user_budgets(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Получение бюджетов пользователя"""
        
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            return []
        
        budgets_data = BudgetQueries.get_active_budgets_with_spending(
            self.session, user.id
        )
        
        return budgets_data
    
    def check_budget_alerts(self, telegram_id: int) -> List[str]:
        """Проверка превышений бюджетов"""
        
        budgets_data = self.get_user_budgets(telegram_id)
        alerts = []
        
        for budget_info in budgets_data:
            budget = budget_info['budget']
            spent_amount = budget_info['spent_amount']
            category_name = budget_info['category_name']
            
            percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
            
            if budget_info['is_exceeded']:
                alerts.append(
                    f"🔴 <b>{budget.name}</b> ({category_name})\n"
                    f"Превышение на {spent_amount - budget.amount} руб."
                )
            elif percentage_used >= 80:
                alerts.append(
                    f"🟡 <b>{budget.name}</b> ({category_name})\n"
                    f"Использовано {percentage_used:.1f}% бюджета"
                )
        
        return alerts
    
    def format_budget_message(self, budget_info: Dict[str, Any]) -> str:
        """Форматирование сообщения о бюджете"""
        budget = budget_info['budget']
        spent_amount = budget_info['spent_amount']
        remaining_amount = budget_info['remaining_amount']
        category_name = budget_info['category_name']
        is_exceeded = budget_info['is_exceeded']
        
        percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
        
        # Определяем статус
        if is_exceeded:
            status_icon = "🔴"
            status_text = "Превышен"
        elif percentage_used >= 80:
            status_icon = "🟡"
            status_text = "Близко к лимиту"
        else:
            status_icon = "🟢"
            status_text = "В норме"
        
        message = (
            f"{status_icon} <b>{budget.name}</b>\n"
            f"📂 Категория: {category_name}\n"
            f"💵 Лимит: {budget.amount} руб.\n"
            f"💸 Потрачено: {spent_amount} руб. ({percentage_used:.1f}%)\n"
            f"💰 Остаток: {remaining_amount} руб.\n"
            f"📊 Статус: {status_text}"
        )
        
        return message 