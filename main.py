"""
Главный файл для запуска Telegram бота
"""

import logging
from typing import NoReturn
from telegram.ext import Application

from app.config import get_config
from app.database import init_database
from app.bot.handlers import setup_handlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Основная функция запуска бота"""
    # Загружаем конфигурацию
    config = get_config()
    logger.info("Конфигурация загружена")
    
    # Инициализируем базу данных
    try:
        init_database()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return
    
    # Создаем приложение бота
    app: Application = Application.builder().token(config.telegram_bot_token).build()
    
    # Настраиваем обработчики
    setup_handlers(app)
    logger.info("Обработчики настроены")
    
    # Запускаем бота
    logger.info("🤖 Бот запускается...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main() 