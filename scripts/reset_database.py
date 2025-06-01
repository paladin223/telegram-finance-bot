#!/usr/bin/env python3
"""
Скрипт для сброса базы данных (удаление и пересоздание)
"""

import sys
import argparse
from pathlib import Path
from typing import NoReturn

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.database import get_session, init_database
from app.database.models import Base, User, Category, Transaction, Budget, Report
from app.database.schemas import TransactionType
from sqlalchemy import text, MetaData


def initialize_session_factory() -> None:
    """Инициализация session factory без создания таблиц"""
    config = get_config()
    
    # Преобразуем асинхронный URL в синхронный
    db_url: str = config.database_url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite:///")
    
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(
        db_url,
        echo=config.debug,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    session_factory = sessionmaker(bind=engine)
    
    # Обновляем глобальные переменные в модуле database
    import app.database.database as db_module
    db_module.engine = engine
    db_module.session_factory = session_factory


def drop_all_tables() -> None:
    """Удаление всех таблиц"""
    print("🗑️ Удаление всех таблиц...")
    
    for session in get_session():
        try:
            # Получаем метаданные базы данных
            metadata = MetaData()
            metadata.reflect(bind=session.bind)
            
            # Удаляем все таблицы в правильном порядке (учитывая foreign keys)
            tables_to_drop = [
                "reports",
                "budgets", 
                "transactions",
                "categories",
                "users"
            ]
            
            for table_name in tables_to_drop:
                if table_name in metadata.tables:
                    print(f"  🗑️ Удаление таблицы {table_name}...")
                    session.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                else:
                    print(f"  ⚠️ Таблица {table_name} не найдена")
            
            session.commit()
            print("✅ Все таблицы удалены")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Ошибка при удалении таблиц: {e}")
            raise


def create_all_tables() -> None:
    """Создание всех таблиц заново"""
    print("🏗️ Создание таблиц...")
    
    try:
        init_database()
        print("✅ Таблицы созданы успешно")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise


def create_sample_data() -> None:
    """Создание примеров данных"""
    print("📝 Создание тестовых данных...")
    
    for session in get_session():
        try:
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
                Category(name="Подарки", transaction_type=TransactionType.INCOME, user_id=test_user.id),
            ]
            
            # Создаем базовые категории расходов
            expense_categories = [
                Category(name="Продукты", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Транспорт", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Развлечения", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Коммунальные", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Здоровье", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Одежда", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
                Category(name="Образование", transaction_type=TransactionType.EXPENSE, user_id=test_user.id),
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


def check_database_status() -> None:
    """Проверка состояния базы данных"""
    print("\n📊 Текущее состояние базы данных:")
    
    try:
        for session in get_session():
            tables_info = [
                ("users", "Пользователи"),
                ("categories", "Категории"),
                ("transactions", "Транзакции"),
                ("budgets", "Бюджеты"),
                ("reports", "Отчеты")
            ]
            
            for table_name, description in tables_info:
                try:
                    count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    print(f"  📋 {table_name}: {count} записей")
                except Exception:
                    print(f"  ❌ {table_name}: таблица не существует")
                    
    except Exception as e:
        print(f"❌ Ошибка при проверке состояния БД: {e}")


def confirm_action(message: str) -> bool:
    """Подтверждение действия пользователем"""
    while True:
        response = input(f"{message} (y/N): ").lower().strip()
        if response in ['y', 'yes', 'да']:
            return True
        elif response in ['n', 'no', 'нет', '']:
            return False
        else:
            print("Пожалуйста, введите 'y' для подтверждения или 'n' для отмены")


def main() -> None:
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description="Сброс базы данных Telegram Finance Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python scripts/reset_database.py                    # Полный сброс с подтверждением
  python scripts/reset_database.py --force            # Без подтверждения
  python scripts/reset_database.py --no-sample-data   # Без тестовых данных
  python scripts/reset_database.py --check-only       # Только проверить состояние
        """
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Не запрашивать подтверждение'
    )
    
    parser.add_argument(
        '--no-sample-data',
        action='store_true',
        help='Не создавать тестовые данные'
    )
    
    parser.add_argument(
        '--check-only', '-c',
        action='store_true',
        help='Только проверить состояние БД, не изменять'
    )
    
    args = parser.parse_args()
    
    print("🗄️ Сброс базы данных Telegram Finance Bot")
    print("=" * 50)
    
    try:
        # Инициализируем session factory
        print("🔧 Инициализация подключения к БД...")
        initialize_session_factory()
        
        # Проверяем конфигурацию
        config = get_config()
        db_name = config.database_url.split('@')[-1].split('/')[1] if '@' in config.database_url else config.database_url
        print(f"🔧 База данных: {db_name}")
        
        # Проверяем текущее состояние
        check_database_status()
        
        if args.check_only:
            print("\n✅ Проверка завершена")
            return
        
        # Предупреждение
        print("\n⚠️ ВНИМАНИЕ: Эта операция удалит ВСЕ данные!")
        print("  • Все пользователи")
        print("  • Все транзакции")
        print("  • Все бюджеты")
        print("  • Все отчеты")
        
        # Запрашиваем подтверждение
        if not args.force:
            if not confirm_action("\n🤔 Вы действительно хотите сбросить базу данных?"):
                print("❌ Операция отменена")
                return
        
        print("\n🚀 Начинаем сброс базы данных...")
        
        # Удаляем все таблицы
        drop_all_tables()
        
        # Создаем таблицы заново
        create_all_tables()
        
        # Создаем тестовые данные (если не отключено)
        if not args.no_sample_data:
            create_sample_data()
        
        # Проверяем финальное состояние
        check_database_status()
        
        print("\n" + "=" * 50)
        print("🎉 Сброс базы данных завершен успешно!")
        
        if not args.no_sample_data:
            print("\n💡 Доступен тестовый пользователь:")
            print("  • Telegram ID: 123456789")
            print("  • Username: testuser")
            print("  • Базовые категории созданы")
        
        print("\n🚀 Теперь можно:")
        print("  • Запустить бота: python main.py")
        print("  • Запустить тесты: pytest")
        
    except KeyboardInterrupt:
        print("\n❌ Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка при сбросе базы данных: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 