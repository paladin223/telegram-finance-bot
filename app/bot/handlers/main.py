"""
Основные обработчики бота
"""

import logging
from typing import NoReturn, Optional
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)

from app.database import get_session
from app.database.queries import UserQueries
from app.bot.keyboards import get_main_keyboard, get_settings_keyboard

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    if not user:
        logger.error("No effective user in start_command")
        return
    
    logger.info(f"Start command called for user {user.id} ({user.first_name})")
    
    for session in get_session():
        try:
            # Проверяем, есть ли пользователь в базе
            logger.info(f"Checking if user {user.id} exists in database")
            existing_user = UserQueries.get_user_by_telegram_id(
                session, user.id
            )
            
            if not existing_user:
                logger.info(f"User {user.id} not found, creating new user")
                # Создаем нового пользователя
                new_user = UserQueries.create_user(
                    session,
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language_code=user.language_code
                )
                logger.info(f"Successfully created user {new_user.id} with telegram_id {new_user.telegram_id}")
                
                welcome_message = (
                    f"👋 Добро пожаловать, {user.first_name}!\n\n"
                    "🏦 Этот бот поможет вам управлять личными финансами:\n"
                    "• 💰 Отслеживать доходы и расходы\n"
                    "• 📊 Создавать бюджеты\n"
                    "• 📈 Генерировать отчеты\n"
                    "• 🔔 Получать уведомления\n\n"
                    "Выберите действие в меню ниже 👇"
                )
            else:
                logger.info(f"User {user.id} found in database (id: {existing_user.id})")
                welcome_message = (
                    f"👋 С возвращением, {user.first_name}!\n\n"
                    "Выберите действие в меню ниже 👇"
                )
            
            if update.message:
                await update.message.reply_text(
                    welcome_message,
                    reply_markup=get_main_keyboard()
                )
            
        except Exception as e:
            logger.error(f"Error in start_command: {e}", exc_info=True)
            if update.message:
                await update.message.reply_text(
                    "❌ Произошла ошибка при инициализации. Попробуйте позже."
                )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "🤖 <b>Команды бота:</b>\n\n"
        "/start - Запуск бота\n"
        "/help - Показать справку\n"
        "/stats - Быстрая статистика\n\n"
        "📋 <b>Основные функции:</b>\n\n"
        "💰 <b>Транзакции:</b>\n"
        "• Добавление доходов и расходов\n"
        "• Категоризация операций\n"
        "• Просмотр истории\n\n"
        "📊 <b>Бюджеты:</b>\n"
        "• Создание бюджетов по категориям\n"
        "• Отслеживание лимитов\n"
        "• Уведомления о превышении\n\n"
        "📈 <b>Отчеты:</b>\n"
        "• Месячные и недельные отчеты\n"
        "• Анализ трат по категориям\n"
        "• Сохранение отчетов\n\n"
        "⚙️ <b>Настройки:</b>\n"
        "• Управление категориями\n"
        "• Настройка уведомлений\n"
        "• Очистка данных\n\n"
        "❓ <b>Примеры использования:</b>\n"
        "• 'Добавить доход' → выбор категории → ввод суммы\n"
        "• 'Мои бюджеты' → просмотр текущих лимитов\n"
        "• 'Отчеты' → выбор типа отчета"
    )
    
    if update.message:
        await update.message.reply_text(help_text, parse_mode='HTML')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /stats"""
    from app.services.transaction_service import TransactionService
    
    user = update.effective_user
    if not user:
        return
    
    for session in get_session():
        try:
            service = TransactionService(session)
            stats = service.get_monthly_statistics(user.id)
            
            stats_message = (
                f"📊 <b>Быстрая статистика за {stats['period']}</b>\n\n"
                f"💰 Доходы: {stats['total_income']} руб.\n"
                f"💸 Расходы: {stats['total_expense']} руб.\n"
                f"💵 Баланс: {stats['balance']} руб.\n\n"
            )
            
            if stats['balance'] > 0:
                stats_message += "✅ Месяц идет успешно!"
            else:
                stats_message += "⚠️ Стоит пересмотреть расходы"
            
            if update.message:
                await update.message.reply_text(stats_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            if update.message:
                await update.message.reply_text(
                    "❌ Не удалось получить статистику"
                )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик основного меню"""
    if not update.message or not update.message.text:
        return
        
    text = update.message.text
    
    # Кнопки, которые обрабатываются специфическими обработчиками
    specific_buttons = {
        "➕ Добавить доход",
        "➖ Добавить расход", 
        "📊 Мои транзакции",
        "💰 Мои бюджеты",
        "📈 Отчеты"
    }
    
    # Если это кнопка со специфическим обработчиком, не обрабатываем здесь
    if text in specific_buttons:
        return
    
    if text == "ℹ️ Помощь":
        await help_command(update, context)
    elif text == "⚙️ Настройки":
        await update.message.reply_text(
            "⚙️ Настройки бота:",
            reply_markup=get_settings_keyboard()
        )
    else:
        await update.message.reply_text(
            "❓ Выберите действие из меню",
            reply_markup=get_main_keyboard()
        )


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик настроек"""
    query = update.callback_query
    if not query or not query.data:
        return
        
    await query.answer()
    
    if query.data == "settings_categories":
        await query.edit_message_text(
            "📂 Управление категориями\n\n"
            "Здесь вы можете управлять своими категориями доходов и расходов.\n"
            "Функция в разработке."
        )
    elif query.data == "settings_notifications":
        await query.edit_message_text(
            "🔔 Настройки уведомлений\n\n"
            "Здесь вы можете настроить уведомления о превышении бюджетов.\n"
            "Функция в разработке."
        )
    elif query.data == "settings_clear_data":
        await query.edit_message_text(
            "🗑️ Очистка данных\n\n"
            "⚠️ Внимание! Эта операция удалит все ваши данные.\n"
            "Функция в разработке."
        )


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик отмены"""
    query = update.callback_query
    if not query:
        return
        
    await query.answer()
    
    await query.edit_message_text(
        "❌ Операция отменена",
        reply_markup=None
    )
    
    # Очищаем состояние пользователя
    if 'user_state' in context.user_data:
        del context.user_data['user_state']


def setup_main_handlers(app: Application) -> None:
    """Настройка основных обработчиков"""
    
    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Обработчики меню
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_main_menu
    ))
    
    # Callback handlers для настроек
    app.add_handler(CallbackQueryHandler(
        handle_settings_callback, pattern="^settings_"
    ))
    
    # Обработчик отмены
    app.add_handler(CallbackQueryHandler(
        handle_cancel, pattern="^cancel$"
    )) 