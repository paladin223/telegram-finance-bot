#!/usr/bin/env python3
"""
Быстрая проверка состояния базы данных
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.database import get_session
from sqlalchemy import text


def main() -> None:
    """Основная функция"""
    print("📊 Состояние базы данных Telegram Finance Bot")
    print("=" * 45)
    
    try:
        # Показываем конфигурацию
        config = get_config()
        db_info = config.database_url.split('@')[-1] if '@' in config.database_url else config.database_url
        print(f"🔧 База данных: {db_info}")
        
        # Проверяем подключение
        for session in get_session():
            session.execute(text("SELECT 1"))
            print("✅ Подключение: Успешно")
            
            # Проверяем таблицы
            tables_info = [
                ("users", "👤 Пользователи"),
                ("categories", "📂 Категории"),
                ("transactions", "💰 Транзакции"),
                ("budgets", "📊 Бюджеты"),
                ("reports", "📈 Отчеты")
            ]
            
            print("\n📋 Таблицы:")
            total_records = 0
            
            for table_name, description in tables_info:
                try:
                    count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    total_records += count
                    status = "✅" if count > 0 else "⚪"
                    print(f"  {status} {description}: {count} записей")
                except Exception:
                    print(f"  ❌ {description}: таблица не найдена")
            
            print(f"\n📊 Общее количество записей: {total_records}")
            
            # Показываем последние активности (если есть данные)
            if total_records > 0:
                try:
                    # Последний пользователь
                    last_user = session.execute(text("""
                        SELECT telegram_id, first_name, created_at 
                        FROM users 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """)).fetchone()
                    
                    if last_user:
                        print(f"\n👤 Последний пользователь: {last_user[1]} (ID: {last_user[0]})")
                    
                    # Последняя транзакция
                    last_transaction = session.execute(text("""
                        SELECT amount, transaction_type, created_at 
                        FROM transactions 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """)).fetchone()
                    
                    if last_transaction:
                        amount = last_transaction[0]
                        t_type = last_transaction[1]
                        emoji = "💰" if t_type == "income" else "💸"
                        print(f"{emoji} Последняя транзакция: {amount} руб. ({t_type})")
                        
                except Exception as e:
                    print(f"⚠️ Не удалось получить детальную информацию: {e}")
            else:
                print("\n💡 База данных пуста. Запустите:")
                print("   python scripts/setup_database.py")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print("\n💡 Возможные причины:")
        print("  • База данных не запущена")
        print("  • Неверные настройки в .env")
        print("  • База данных не инициализирована")
        sys.exit(1)


if __name__ == "__main__":
    main() 