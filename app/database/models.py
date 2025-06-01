"""
SQLAlchemy модели с современным маппингом
"""

from datetime import datetime
from typing import List, Optional, Annotated

from sqlalchemy import String, DateTime, Numeric, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .schemas import TransactionType, ReportType


# Создаем базовый класс
class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


# Определяем типы для переиспользования
intpk = Annotated[int, mapped_column(primary_key=True)]
str255 = Annotated[str, mapped_column(String(255))]
str255_nullable = Annotated[Optional[str], mapped_column(String(255), nullable=True)]
str10_nullable = Annotated[Optional[str], mapped_column(String(10), nullable=True)]
text_nullable = Annotated[Optional[str], mapped_column(Text, nullable=True)]
decimal_amount = Annotated[float, mapped_column(Numeric(15, 2))]
decimal_amount_default = Annotated[float, mapped_column(Numeric(15, 2), default=0)]
bool_active = Annotated[bool, mapped_column(Boolean, default=True)]
datetime_now = Annotated[datetime, mapped_column(DateTime, default=datetime.utcnow)]
datetime_now_update = Annotated[datetime, mapped_column(
    DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
)]


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    username: Mapped[str255_nullable]
    first_name: Mapped[str255_nullable]
    last_name: Mapped[str255_nullable]
    language_code: Mapped[str10_nullable]
    created_at: Mapped[datetime_now]
    updated_at: Mapped[datetime_now_update]
    is_active: Mapped[bool_active]

    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    reports: Mapped[List["Report"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="select"
    )


class Category(Base):
    """Модель категории"""
    __tablename__ = "categories"

    id: Mapped[intpk]
    name: Mapped[str255]
    description: Mapped[text_nullable]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    created_at: Mapped[datetime_now]
    is_active: Mapped[bool_active]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="categories", lazy="select")
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="category", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="category", 
        cascade="all, delete-orphan",
        lazy="select"
    )


class Transaction(Base):
    """Модель транзакции"""
    __tablename__ = "transactions"

    id: Mapped[intpk]
    amount: Mapped[decimal_amount]
    description: Mapped[text_nullable]
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    created_at: Mapped[datetime_now]
    transaction_date: Mapped[datetime_now]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="transactions", lazy="select")
    category: Mapped["Category"] = relationship(back_populates="transactions", lazy="select")


class Budget(Base):
    """Модель бюджета"""
    __tablename__ = "budgets"

    id: Mapped[intpk]
    name: Mapped[str255]
    amount: Mapped[decimal_amount]
    spent_amount: Mapped[decimal_amount_default]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime_now]
    is_active: Mapped[bool_active]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="budgets", lazy="select")
    category: Mapped["Category"] = relationship(back_populates="budgets", lazy="select")


class Report(Base):
    """Модель отчета"""
    __tablename__ = "reports"

    id: Mapped[intpk]
    name: Mapped[str255]
    report_type: Mapped[ReportType] = mapped_column(SQLEnum(ReportType), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data: Mapped[text_nullable]  # JSON данные отчета
    created_at: Mapped[datetime_now]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="reports", lazy="select") 