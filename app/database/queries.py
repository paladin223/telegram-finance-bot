"""
Модуль с запросами к базе данных
Содержит минимум 10 запросов с полной типизацией
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from .models import User, Category, Transaction, Budget, Report
from .schemas import TransactionType, ReportType


class UserQueries:
    """Запросы для работы с пользователями"""
    
    @staticmethod
    def create_user(session: Session, telegram_id: int, 
                         username: Optional[str] = None,
                         first_name: Optional[str] = None,
                         last_name: Optional[str] = None,
                         language_code: Optional[str] = None) -> User:
        """1. Создание нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_telegram_id(session: Session, telegram_id: int) -> Optional[User]:
        """2. Получение пользователя по telegram_id"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_user_with_relations(session: Session, user_id: int) -> Optional[User]:
        """3. Получение пользователя со всеми связанными данными"""
        stmt = (
            select(User)
            .options(
                selectinload(User.categories),
                selectinload(User.transactions),
                selectinload(User.budgets),
                selectinload(User.reports)
            )
            .where(User.id == user_id)
        )
        result = session.execute(stmt)
        return result.scalar_one_or_none()


class CategoryQueries:
    """Запросы для работы с категориями"""
    
    @staticmethod
    def create_category(session: Session, name: str, user_id: int,
                             transaction_type: TransactionType,
                             description: Optional[str] = None) -> Category:
        """4. Создание новой категории"""
        category = Category(
            name=name,
            description=description,
            user_id=user_id,
            transaction_type=transaction_type
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    
    @staticmethod
    def get_user_categories(session: Session, user_id: int,
                                 transaction_type: Optional[TransactionType] = None) -> List[Category]:
        """5. Получение категорий пользователя по типу"""
        stmt = select(Category).where(
            and_(
                Category.user_id == user_id,
                Category.is_active == True
            )
        )
        
        if transaction_type:
            stmt = stmt.where(Category.transaction_type == transaction_type)
            
        stmt = stmt.order_by(Category.name)
        result = session.execute(stmt)
        return result.scalars().all()


class TransactionQueries:
    """Запросы для работы с транзакциями"""
    
    @staticmethod
    def create_transaction(session: Session, amount: Decimal, user_id: int,
                               category_id: int, transaction_type: TransactionType,
                               description: Optional[str] = None,
                               transaction_date: Optional[datetime] = None) -> Transaction:
        """6. Создание новой транзакции"""
        transaction = Transaction(
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            user_id=user_id,
            category_id=category_id,
            transaction_date=transaction_date or datetime.utcnow()
        )
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction
    
    @staticmethod
    def get_user_transactions(session: Session, user_id: int,
                                   limit: int = 50, offset: int = 0,
                                   transaction_type: Optional[TransactionType] = None,
                                   category_id: Optional[int] = None,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> List[Transaction]:
        """7. Получение транзакций пользователя с фильтрацией"""
        stmt = (
            select(Transaction)
            .options(selectinload(Transaction.category))
            .where(Transaction.user_id == user_id)
        )
        
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type)
        
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
            
        if start_date:
            stmt = stmt.where(Transaction.transaction_date >= start_date)
            
        if end_date:
            stmt = stmt.where(Transaction.transaction_date <= end_date)
        
        stmt = stmt.order_by(desc(Transaction.transaction_date)).limit(limit).offset(offset)
        result = session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    def get_transactions_sum_by_category(session: Session, user_id: int,
                                             start_date: datetime, end_date: datetime,
                                             transaction_type: TransactionType) -> List[Dict[str, Any]]:
        """8. Получение суммы транзакций по категориям за период"""
        stmt = (
            select(
                Category.name.label('category_name'),
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_type == transaction_type,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date
                )
            )
            .group_by(Category.id, Category.name)
            .order_by(desc('total_amount'))
        )
        
        result = session.execute(stmt)
        return [
            {
                'category_name': row.category_name,
                'total_amount': row.total_amount,
                'transaction_count': row.transaction_count
            }
            for row in result
        ]


class BudgetQueries:
    """Запросы для работы с бюджетами"""
    
    @staticmethod
    def create_budget(session: Session, name: str, amount: Decimal,
                           user_id: int, category_id: int,
                           start_date: datetime, end_date: datetime) -> Budget:
        """9. Создание нового бюджета"""
        budget = Budget(
            name=name,
            amount=amount,
            user_id=user_id,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date
        )
        session.add(budget)
        session.commit()
        session.refresh(budget)
        return budget
    
    @staticmethod
    def get_active_budgets_with_spending(session: Session, user_id: int) -> List[Dict[str, Any]]:
        """10. Получение активных бюджетов с текущими тратами"""
        current_date = datetime.utcnow()
        
        # Получаем все активные бюджеты
        budgets_stmt = (
            select(Budget, Category.name.label('category_name'))
            .join(Category, Budget.category_id == Category.id)
            .where(
                and_(
                    Budget.user_id == user_id,
                    Budget.is_active == True,
                    or_(
                        Budget.end_date.is_(None),
                        Budget.end_date >= current_date
                    )
                )
            )
            .order_by(Budget.name)
        )
        
        result = session.execute(budgets_stmt)
        budgets_data = []
        
        for row in result:
            budget = row.Budget
            category_name = row.category_name
            
            # Для каждого бюджета отдельно считаем потраченную сумму
            spent_stmt = (
                select(func.sum(Transaction.amount))
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.category_id == budget.category_id,
                        Transaction.transaction_type == TransactionType.EXPENSE,
                        Transaction.transaction_date >= budget.start_date,
                        Transaction.transaction_date <= budget.end_date
                    )
                )
            )
            
            spent_amount = session.execute(spent_stmt).scalar() or Decimal('0')
            remaining_amount = budget.amount - spent_amount
            is_exceeded = spent_amount > budget.amount
            
            budgets_data.append({
                'budget': budget,
                'category_name': category_name,
                'spent_amount': spent_amount,
                'remaining_amount': remaining_amount,
                'is_exceeded': is_exceeded
            })
        
        return budgets_data


class ReportQueries:
    """Запросы для работы с отчетами"""
    
    @staticmethod
    def create_report(session: Session, name: str, user_id: int,
                           report_type: ReportType, start_date: datetime,
                           end_date: datetime, data: str) -> Report:
        """11. Создание нового отчета"""
        report = Report(
            name=name,
            user_id=user_id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            data=data
        )
        session.add(report)
        session.commit()
        session.refresh(report)
        return report
    
    @staticmethod
    def get_user_reports(session: Session, user_id: int,
                              report_type: Optional[ReportType] = None) -> List[Report]:
        """12. Получение отчетов пользователя"""
        stmt = select(Report).where(Report.user_id == user_id)
        
        if report_type:
            stmt = stmt.where(Report.report_type == report_type)
            
        stmt = stmt.order_by(desc(Report.created_at))
        result = session.execute(stmt)
        return result.scalars().all()


class AnalyticsQueries:
    """Запросы для аналитики"""
    
    @staticmethod
    def get_monthly_summary(session: Session, user_id: int,
                                 year: int, month: int) -> Dict[str, Any]:
        """13. Получение месячной сводки"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Получаем суммы доходов и расходов
        income_stmt = (
            select(func.sum(Transaction.amount))
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_type == TransactionType.INCOME,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date < end_date
                )
            )
        )
        
        expense_stmt = (
            select(func.sum(Transaction.amount))
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_type == TransactionType.EXPENSE,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date < end_date
                )
            )
        )
        
        total_income = session.execute(income_stmt).scalar() or Decimal('0')
        total_expenses = session.execute(expense_stmt).scalar() or Decimal('0')
        
        # Получаем топ категории расходов
        top_categories = TransactionQueries.get_transactions_sum_by_category(
            session, user_id, start_date, end_date, TransactionType.EXPENSE
        )
        
        return {
            'year': year,
            'month': month,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': total_income - total_expenses,
            'top_expense_categories': top_categories[:5]  # Топ 5 категорий
        }
    
    @staticmethod
    def get_top_expense_categories(session: Session, user_id: int,
                                       start_date: datetime, end_date: datetime,
                                       limit: int = 5) -> List[Dict[str, Any]]:
        """14. Получение топ категорий расходов за период"""
        return TransactionQueries.get_transactions_sum_by_category(
            session, user_id, start_date, end_date, TransactionType.EXPENSE
        )[:limit] 