#!/usr/bin/env python3
"""
Тестовый скрипт для проверки создания пользователей
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.database import get_session, init_database
from app.database.queries import UserQueries


def test_user_creation():
    """Тестирование создания пользователя"""
    print("🧪 Тестирование создания пользователей")
    print("=" * 40)
    
    try:
        # Инициализируем базу данных
        print("🔧 Инициализация базы данных...")
        init_database()
        print("✅ База данных инициализирована")
        
        # Тестируем создание пользователя
        test_telegram_id = 974824380  # ID из логов
        
        for session in get_session():
            # Проверяем, есть ли пользователь
            print(f"🔍 Проверяем пользователя {test_telegram_id}...")
            existing_user = UserQueries.get_user_by_telegram_id(session, test_telegram_id)
            
            if existing_user:
                print(f"✅ Пользователь найден: ID={existing_user.id}, telegram_id={existing_user.telegram_id}")
                print(f"   Имя: {existing_user.first_name} {existing_user.last_name}")
                print(f"   Username: {existing_user.username}")
            else:
                print("❌ Пользователь не найден")
                
                # Создаем пользователя
                print("📝 Создаем пользователя...")
                new_user = UserQueries.create_user(
                    session,
                    telegram_id=test_telegram_id,
                    username="testuser_real",
                    first_name="Реальный",
                    last_name="Пользователь",
                    language_code="ru"
                )
                print(f"✅ Пользователь создан: ID={new_user.id}, telegram_id={new_user.telegram_id}")
                
                # Проверяем еще раз
                check_user = UserQueries.get_user_by_telegram_id(session, test_telegram_id)
                if check_user:
                    print("✅ Пользователь успешно найден после создания")
                else:
                    print("❌ Ошибка: пользователь не найден после создания")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_user_creation() 