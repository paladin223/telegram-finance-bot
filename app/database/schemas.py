"""
Python схемы (dataclasses) для моделей данных
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class TransactionType(Enum):
    """Тип транзакции"""
    INCOME = "income"
    EXPENSE = "expense"


class ReportType(Enum):
    """Тип отчета"""
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    CUSTOM = "custom"


@dataclass
class User:
    """Схема пользователя"""
    id: Optional[int] = None
    telegram_id: int = 0
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Relationships
    categories: List["Category"] = field(default_factory=list)
    transactions: List["Transaction"] = field(default_factory=list)
    budgets: List["Budget"] = field(default_factory=list)
    reports: List["Report"] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.username or f"User {self.telegram_id}"


@dataclass
class Category:
    """Схема категории"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    user_id: int = 0
    transaction_type: TransactionType = TransactionType.EXPENSE
    created_at: Optional[datetime] = None
    is_active: bool = True
    
    # Relationships
    user: Optional[User] = None
    transactions: List["Transaction"] = field(default_factory=list)
    budgets: List["Budget"] = field(default_factory=list)

    @property
    def type_icon(self) -> str:
        """Иконка для типа категории"""
        return "📈" if self.transaction_type == TransactionType.INCOME else "📉"


@dataclass
class Transaction:
    """Схема транзакции"""
    id: Optional[int] = None
    amount: Decimal = Decimal("0.00")
    description: Optional[str] = None
    transaction_type: TransactionType = TransactionType.EXPENSE
    user_id: int = 0
    category_id: int = 0
    created_at: Optional[datetime] = None
    transaction_date: Optional[datetime] = None
    
    # Relationships
    user: Optional[User] = None
    category: Optional[Category] = None

    @property
    def formatted_amount(self) -> str:
        """Отформатированная сумма с валютой"""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        return f"{sign}{self.amount} ₽"

    @property
    def type_icon(self) -> str:
        """Иконка для типа транзакции"""
        return "➕" if self.transaction_type == TransactionType.INCOME else "➖"


@dataclass
class Budget:
    """Схема бюджета"""
    id: Optional[int] = None
    name: str = ""
    amount: Decimal = Decimal("0.00")
    spent_amount: Decimal = Decimal("0.00")
    user_id: int = 0
    category_id: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_active: bool = True
    
    # Relationships
    user: Optional[User] = None
    category: Optional[Category] = None

    @property
    def remaining_amount(self) -> Decimal:
        """Оставшаяся сумма бюджета"""
        return self.amount - self.spent_amount

    @property
    def percentage_used(self) -> float:
        """Процент использования бюджета"""
        if self.amount == 0:
            return 0.0
        return float((self.spent_amount / self.amount) * 100)

    @property
    def is_exceeded(self) -> bool:
        """Превышен ли бюджет"""
        return self.spent_amount > self.amount

    @property
    def status_icon(self) -> str:
        """Иконка статуса бюджета"""
        percentage = self.percentage_used
        if percentage >= 100:
            return "🔴"  # Превышен
        elif percentage >= 80:
            return "🟡"  # Близко к лимиту
        else:
            return "🟢"  # В норме


@dataclass
class Report:
    """Схема отчета"""
    id: Optional[int] = None
    name: str = ""
    report_type: ReportType = ReportType.MONTHLY
    user_id: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    data: Optional[str] = None  # JSON данные
    created_at: Optional[datetime] = None
    
    # Relationships
    user: Optional[User] = None

    @property
    def type_icon(self) -> str:
        """Иконка для типа отчета"""
        icons = {
            ReportType.MONTHLY: "📊",
            ReportType.WEEKLY: "📈",
            ReportType.CUSTOM: "📋"
        }
        return icons.get(self.report_type, "📄")

    @property
    def period_description(self) -> str:
        """Описание периода отчета"""
        if not self.start_date or not self.end_date:
            return "Период не указан"
        
        start = self.start_date.strftime("%d.%m.%Y")
        end = self.end_date.strftime("%d.%m.%Y")
        return f"{start} - {end}" 