"""
Сервис для работы с отчетами
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.database.schemas import Report, ReportType, TransactionType
from app.database.queries import (
    ReportQueries, UserQueries, TransactionQueries, AnalyticsQueries
)


class ReportService:
    """Сервис для работы с отчетами"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def generate_monthly_report(self, telegram_id: int,
                               year: Optional[int] = None,
                               month: Optional[int] = None,
                               save_report: bool = True) -> str:
        """Генерация месячного отчета"""
        
        # Получаем пользователя
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Определяем период
        now = datetime.utcnow()
        target_year = year or now.year
        target_month = month or now.month
        
        # Получаем данные
        summary = AnalyticsQueries.get_monthly_summary(
            self.session, user.id, target_year, target_month
        )
        
        top_expenses = AnalyticsQueries.get_top_expense_categories(
            self.session, user.id,
            datetime(target_year, target_month, 1),
            datetime(target_year + 1, 1, 1) if target_month == 12 else datetime(target_year, target_month + 1, 1),
            limit=5
        )
        
        # Сохраняем отчет если нужно
        if save_report:
            report_name = f"Месячный отчет {target_year}-{target_month:02d}"
            report = ReportQueries.create_report(
                self.session,
                name=report_name,
                user_id=user.id,
                report_type=ReportType.MONTHLY,
                start_date=datetime(target_year, target_month, 1),
                end_date=datetime(target_year + 1, 1, 1) if target_month == 12 else datetime(target_year, target_month + 1, 1),
                data=str(summary)  # Простое сохранение данных как строка
            )
        
        return self._format_monthly_report(summary, top_expenses)
    
    def generate_weekly_report(self, telegram_id: int) -> str:
        """Генерация недельного отчета"""
        
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Определяем период (последние 7 дней)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Получаем транзакции за неделю
        transactions = TransactionQueries.get_user_transactions(
            self.session,
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            limit=100
        )
        
        # Группируем по дням
        daily_stats = {}
        for transaction in transactions:
            date_key = transaction.transaction_date.strftime("%Y-%m-%d")
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'income': Decimal('0'),
                    'expense': Decimal('0'),
                    'transactions_count': 0
                }
            
            if transaction.transaction_type == TransactionType.INCOME:
                daily_stats[date_key]['income'] += transaction.amount
            else:
                daily_stats[date_key]['expense'] += transaction.amount
            
            daily_stats[date_key]['transactions_count'] += 1
        
        # Сохраняем отчет
        report_name = f"Недельный отчет {start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')}"
        report = ReportQueries.create_report(
            self.session,
            name=report_name,
            user_id=user.id,
            report_type=ReportType.WEEKLY,
            start_date=start_date,
            end_date=end_date,
            data=str(daily_stats)
        )
        
        return self._format_weekly_report(daily_stats, start_date, end_date)
    
    def generate_categories_report(self, telegram_id: int) -> str:
        """Генерация отчета по категориям"""
        
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Период - текущий месяц
        now = datetime.utcnow()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime(now.year, now.month + 1, 1)
        
        # Получаем данные по категориям
        expense_categories = TransactionQueries.get_transactions_sum_by_category(
            self.session, user.id, start_date, end_date, TransactionType.EXPENSE
        )
        
        income_categories = TransactionQueries.get_transactions_sum_by_category(
            self.session, user.id, start_date, end_date, TransactionType.INCOME
        )
        
        message = f"📊 <b>Отчет по категориям за {now.strftime('%m.%Y')}</b>\n\n"
        
        if expense_categories:
            message += "💸 <b>Расходы:</b>\n"
            for cat in expense_categories:
                message += f"• {cat['category_name']}: {cat['total_amount']} руб.\n"
            message += "\n"
        
        if income_categories:
            message += "💰 <b>Доходы:</b>\n"
            for cat in income_categories:
                message += f"• {cat['category_name']}: {cat['total_amount']} руб.\n"
        
        if not expense_categories and not income_categories:
            message += "Транзакций за текущий месяц не найдено."
        
        return message
    
    def get_user_reports(self, telegram_id: int, limit: int = 10) -> List[Report]:
        """Получение отчетов пользователя"""
        
        user = UserQueries.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            return []
        
        reports = ReportQueries.get_user_reports(self.session, user.id)
        return reports[:limit]
    
    def _format_monthly_report(self, summary: Dict[str, Any],
                              top_expenses: List[Dict[str, Any]]) -> str:
        """Форматирование месячного отчета"""
        
        message = (
            f"📊 <b>Месячный отчет за {summary['year']}-{summary['month']:02d}</b>\n\n"
            f"💰 Доходы: {summary['total_income']} руб.\n"
            f"💸 Расходы: {summary['total_expenses']} руб.\n"
            f"💵 Баланс: {summary['balance']} руб.\n\n"
        )
        
        if summary['balance'] > 0:
            message += "✅ Отличный месяц! Доходы превышают расходы.\n\n"
        elif summary['balance'] == 0:
            message += "📊 Доходы и расходы сбалансированы.\n\n"
        else:
            message += "⚠️ Расходы превышают доходы. Стоит пересмотреть бюджет.\n\n"
        
        if top_expenses:
            message += "📈 <b>Топ категорий расходов:</b>\n"
            for i, expense in enumerate(top_expenses, 1):
                message += f"{i}. {expense['category_name']}: {expense['total_amount']} руб.\n"
        
        return message
    
    def _format_weekly_report(self, daily_stats: Dict[str, Dict],
                             start_date: datetime, end_date: datetime) -> str:
        """Форматирование недельного отчета"""
        
        message = (
            f"📅 <b>Недельный отчет</b>\n"
            f"📆 {start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')}\n\n"
        )
        
        total_income = Decimal('0')
        total_expense = Decimal('0')
        total_transactions = 0
        
        # Подсчитываем общие суммы
        for date_key, stats in daily_stats.items():
            total_income += stats['income']
            total_expense += stats['expense']
            total_transactions += stats['transactions_count']
        
        message += (
            f"💰 Общие доходы: {total_income} руб.\n"
            f"💸 Общие расходы: {total_expense} руб.\n"
            f"💵 Баланс: {total_income - total_expense} руб.\n"
            f"📊 Всего транзакций: {total_transactions}\n\n"
        )
        
        if daily_stats:
            message += "📈 <b>По дням:</b>\n"
            for date_key in sorted(daily_stats.keys()):
                stats = daily_stats[date_key]
                date_obj = datetime.strptime(date_key, "%Y-%m-%d")
                message += (
                    f"• {date_obj.strftime('%d.%m')}: "
                    f"+{stats['income']} / -{stats['expense']} руб. "
                    f"({stats['transactions_count']} операций)\n"
                )
        else:
            message += "За эту неделю транзакций не было."
        
        return message 