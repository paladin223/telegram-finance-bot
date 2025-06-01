"""
Обработчики для работы с транзакциями
"""

import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

from app.database import get_session
from app.database.schemas import TransactionType
from app.database.queries import CategoryQueries
from app.services.transaction_service import TransactionService
from app.bot.keyboards import (
    get_main_keyboard, get_categories_keyboard, get_cancel_keyboard
)

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_AMOUNT, WAITING_DESCRIPTION, WAITING_CATEGORY = range(3)


async def add_income_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало добавления дохода"""
    if update.message.text == "➕ Добавить доход":
        context.user_data['transaction_type'] = TransactionType.INCOME
        
        # Создаем специальную клавиатуру с уникальным паттерном
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💰 Добавление дохода\n\n"
            "Введите сумму дохода в рублях:",
            reply_markup=cancel_keyboard
        )
        return WAITING_AMOUNT
    
    return ConversationHandler.END


async def add_expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало добавления расхода"""
    if update.message.text == "➖ Добавить расход":
        context.user_data['transaction_type'] = TransactionType.EXPENSE
        
        # Создаем специальную клавиатуру с уникальным паттерном
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💸 Добавление расхода\n\n"
            "Введите сумму расхода в рублях:",
            reply_markup=cancel_keyboard
        )
        return WAITING_AMOUNT
    
    return ConversationHandler.END


async def amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода суммы"""
    try:
        amount_text = update.message.text.replace(',', '.').strip()
        amount = Decimal(amount_text)
        
        if amount <= 0:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
            ]
            cancel_keyboard = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Сумма должна быть больше 0. Попробуйте снова:",
                reply_markup=cancel_keyboard
            )
            return WAITING_AMOUNT
        
        context.user_data['amount'] = amount
        
        # Получаем категории пользователя
        user = update.effective_user
        transaction_type = context.user_data['transaction_type']
        
        for session in get_session():
            categories = CategoryQueries.get_user_categories(
                session, user.id, transaction_type
            )
            
            if categories:
                category_names = [cat.name for cat in categories]
                # Создаем клавиатуру с кнопкой отмены
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = []
                
                for category in category_names:
                    keyboard.append([
                        InlineKeyboardButton(category, callback_data=f"category_{category}")
                    ])
                
                keyboard.append([
                    InlineKeyboardButton("📝 Другая категория", callback_data="category_other")
                ])
                keyboard.append([
                    InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")
                ])
                
                categories_keyboard = InlineKeyboardMarkup(keyboard)
                
                # Правильное форматирование для русского языка
                type_text = "дохода" if transaction_type == TransactionType.INCOME else "расхода"
                await update.message.reply_text(
                    f"📂 Выберите категорию для {type_text}:",
                    reply_markup=categories_keyboard
                )
                return WAITING_CATEGORY
            else:
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
                ]
                cancel_keyboard = InlineKeyboardMarkup(keyboard)
                
                type_text = "дохода" if transaction_type == TransactionType.INCOME else "расхода"
                await update.message.reply_text(
                    f"📝 Введите название категории для {type_text}:",
                    reply_markup=cancel_keyboard
                )
                return WAITING_CATEGORY
    
    except (InvalidOperation, ValueError):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Неверный формат суммы. Введите число (например: 1500 или 150.50):",
            reply_markup=cancel_keyboard
        )
        return WAITING_AMOUNT


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора категории"""
    if update.callback_query:
        # Обработка callback от кнопки
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("category_"):
            category_name = query.data.replace("category_", "")
            
            if category_name == "other":
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
                ]
                cancel_keyboard = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📝 Введите название новой категории:",
                    reply_markup=cancel_keyboard
                )
                return WAITING_CATEGORY
            else:
                context.user_data['category_name'] = category_name
                
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
                ]
                cancel_keyboard = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📝 Введите описание транзакции:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⏭️ Пропустить", callback_data="description_skip")],
                        [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
                    ])
                )
                return WAITING_DESCRIPTION
    else:
        # Обработка текстового ввода категории
        category_name = update.message.text.strip()
        context.user_data['category_name'] = category_name
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 Введите описание транзакции:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭️ Пропустить", callback_data="description_skip")],
                [InlineKeyboardButton("❌ Отмена", callback_data="transaction_cancel")]
            ])
        )
        return WAITING_DESCRIPTION
    
    return WAITING_CATEGORY


async def description_skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка пропуска описания"""
    query = update.callback_query
    await query.answer()
    
    # Создаем транзакцию без описания
    user = update.effective_user
    amount = context.user_data['amount']
    category_name = context.user_data['category_name']
    transaction_type = context.user_data['transaction_type']
    
    for session in get_session():
        try:
            service = TransactionService(session)
            transaction = service.add_transaction(
                telegram_id=user.id,
                amount=amount,
                category_name=category_name,
                transaction_type=transaction_type,
                description=None
            )
            
            # Форматируем сообщение о созданной транзакции
            message = service.format_transaction_message(transaction)
            
            await query.edit_message_text(
                f"✅ Транзакция успешно добавлена!\n\n{message}",
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            await query.edit_message_text(
                "❌ Ошибка при создании транзакции. Попробуйте позже."
            )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка описания и создание транзакции"""
    description = update.message.text.strip()
    
    if description.lower() in ['пропустить', 'skip', '-']:
        description = None
    
    # Создаем транзакцию
    user = update.effective_user
    amount = context.user_data['amount']
    category_name = context.user_data['category_name']
    transaction_type = context.user_data['transaction_type']
    
    for session in get_session():
        try:
            service = TransactionService(session)
            transaction = service.add_transaction(
                telegram_id=user.id,
                amount=amount,
                category_name=category_name,
                transaction_type=transaction_type,
                description=description
            )
            
            # Форматируем сообщение о созданной транзакции
            message = service.format_transaction_message(transaction)
            
            await update.message.reply_text(
                f"✅ Транзакция успешно добавлена!\n\n{message}",
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            await update.message.reply_text(
                "❌ Ошибка при создании транзакции. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


async def view_transactions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просмотр транзакций"""
    if update.message.text == "📊 Мои транзакции":
        user = update.effective_user
        
        for session in get_session():
            try:
                service = TransactionService(session)
                transactions = service.get_user_transactions(
                    telegram_id=user.id,
                    limit=10
                )
                
                if not transactions:
                    await update.message.reply_text(
                        "📋 У вас пока нет транзакций.\n"
                        "Используйте кнопки меню для добавления доходов или расходов."
                    )
                    return
                
                message = "📊 <b>Последние 10 транзакций:</b>\n\n"
                
                for i, transaction in enumerate(transactions, 1):
                    type_emoji = "💰" if transaction.transaction_type == TransactionType.INCOME else "💸"
                    
                    message += (
                        f"{i}. {type_emoji} {transaction.amount} руб. - "
                        f"{transaction.category.name if transaction.category else 'Без категории'}\n"
                        f"   📅 {transaction.transaction_date.strftime('%d.%m.%Y %H:%M')}\n"
                    )
                    
                    if transaction.description:
                        message += f"   📝 {transaction.description}\n"
                    
                    message += "\n"
                
                await update.message.reply_text(message, parse_mode='HTML')
                
            except Exception as e:
                logger.error(f"Error viewing transactions: {e}")
                await update.message.reply_text(
                    "❌ Ошибка при получении транзакций"
                )


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ Операция отменена"
        )
    else:
        await update.message.reply_text(
            "❌ Операция отменена",
            reply_markup=get_main_keyboard()
        )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


def setup_transaction_handlers(app: Application) -> None:
    """Настройка обработчиков транзакций"""
    
    # ConversationHandler для добавления доходов
    income_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^➕ Добавить доход$"), 
                add_income_handler
            )
        ],
        states={
            WAITING_AMOUNT: [
                CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_handler)
            ],
            WAITING_CATEGORY: [
                CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler),
                CallbackQueryHandler(category_handler, pattern="^category_")
            ],
            WAITING_DESCRIPTION: [
                CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
                CallbackQueryHandler(description_skip_handler, pattern="^description_skip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
            MessageHandler(filters.COMMAND, cancel_handler),
            MessageHandler(
                filters.Regex("^(💰 Мои бюджеты|📊 Мои транзакции|📈 Отчеты|⚙️ Настройки|ℹ️ Помощь|➖ Добавить расход)$"), 
                cancel_handler
            )
        ],
        per_chat=True,
        per_user=True
    )
    
    # ConversationHandler для добавления расходов
    expense_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^➖ Добавить расход$"), 
                add_expense_handler
            )
        ],
        states={
            WAITING_AMOUNT: [
                CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_handler)
            ],
            WAITING_CATEGORY: [
                CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler),
                CallbackQueryHandler(category_handler, pattern="^category_")
            ],
            WAITING_DESCRIPTION: [
                CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
                CallbackQueryHandler(description_skip_handler, pattern="^description_skip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_handler, pattern="^transaction_cancel$"),
            MessageHandler(filters.COMMAND, cancel_handler),
            MessageHandler(
                filters.Regex("^(💰 Мои бюджеты|📊 Мои транзакции|📈 Отчеты|⚙️ Настройки|ℹ️ Помощь|➕ Добавить доход)$"), 
                cancel_handler
            )
        ],
        per_chat=True,
        per_user=True
    )
    
    # Просмотр транзакций
    app.add_handler(MessageHandler(
        filters.Regex("^📊 Мои транзакции$"),
        view_transactions_handler
    ))
    
    # Добавляем conversation handlers
    app.add_handler(income_conv_handler)
    app.add_handler(expense_conv_handler) 