#!/usr/bin/env python3
"""
Скрипт для настройки базы данных
"""

import os
import sys
from pathlib import Path
from typing import NoReturn

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.database import init_database, get_session
from app.database.models import User, Category, Transaction, Budget, Report
from app.database.schemas import TransactionType
from sqlalchemy import text


def create_sample_data() -> None:
    """Создание тестовых данных"""
    print("📝 Создание примеров данных...")
    
    for session in get_session():
        try:
            # Проверяем, есть ли уже данные
            existing_users = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            if existing_users > 0:
                print("✅ Данные уже существуют, пропускаем создание примеров")
                return
            
            # Создаем тестового пользователя
            test_user = User(
                telegram_id=123456789,
                username="testuser",
                first_name="Тест",
                last_name="Пользователь",
                language_code="ru"
            )
            session.add(test_user)
            session.flush()  # Получаем ID пользователя
            
            # Создаем базовые категории доходов
            income_categories = [
                Category(name="Зарплата", transaction_type=TransactionType.INCOME, user_id=test_user.id),
                Category(name="Фриланс", transaction_type=TransactionType.INCOME, user_id=test_user.id),
                Category(name="Инвестиции", transaction_type=TransactionType.INCOME, user_id=test_user.id),
            ]
            
            # Создаем базовые категории расходов
            expense_categories = [
                Category(name="Продукты", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Транспорт", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Развлечения", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Коммунальные", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Здоровье", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
            ]
            
            all_categories = income_categories + expense_categories
            session.add_all(all_categories)
            session.commit()
            
            print(f"✅ Создан тестовый пользователь: {test_user.username}")
            print(f"✅ Создано {len(income_categories)} категорий доходов")
            print(f"✅ Создано {len(expense_categories)} категорий расходов")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Ошибка при создании тестовых данных: {e}")
            raise


def check_database_connection() -> bool:
    """Проверка подключения к базе данных"""
    try:
        for session in get_session():
            # Простая проверка подключения
            session.execute(text("SELECT 1"))
            print("✅ Подключение к базе данных успешно")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False


def show_database_info() -> None:
    """Показать информацию о созданных таблицах"""
    print("\n📊 Информация о базе данных:")
    
    for session in get_session():
        try:
            # Проверяем созданные таблицы
            tables_info = [
                ("users", "Пользователи бота"),
                ("categories", "Категории доходов/расходов"),
                ("transactions", "Финансовые операции"),
                ("budgets", "Бюджеты по категориям"),
                ("reports", "Сохраненные отчеты")
            ]
            
            for table_name, description in tables_info:
                try:
                    count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    print(f"  📋 {table_name}: {description} ({count} записей)")
                except Exception:
                    print(f"  ❌ {table_name}: таблица не найдена")
                    
        except Exception as e:
            print(f"❌ Ошибка при получении информации о БД: {e}")


def main() -> None:
    """Основная функция"""
    print("🗄️ Настройка базы данных для Telegram Finance Bot")
    print("=" * 60)
    
    try:
        # Проверяем конфигурацию
        config = get_config()
        print(f"🔧 База данных: {config.database_url.split('@')[-1] if '@' in config.database_url else config.database_url}")
        
        # Инициализируем базу данных (создаем таблицы)
        print("📦 Инициализация базы данных...")
        init_database()
        print("✅ Таблицы созданы успешно")
        
        # Проверяем подключение
        if not check_database_connection():
            sys.exit(1)
        
        # Создаем тестовые данные
        create_sample_data()
        
        # Показываем информацию
        show_database_info()
        
        print("\n" + "=" * 60)
        print("🎉 Настройка базы данных завершена успешно!")
        print("\n💡 Теперь вы можете:")
        print("   • Запустить бота: python main.py")
        print("   • Запустить тесты: pytest")
        print("   • Проверить типы: mypy app/ main.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка при настройке базы данных: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 