"""
Обработчики для работы с бюджетами
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)

from app.database import get_session
from app.services.budget_service import BudgetService
from app.database.queries import CategoryQueries, UserQueries
from app.database.schemas import TransactionType
from app.bot.keyboards import get_budget_keyboard, get_categories_keyboard, get_cancel_keyboard

logger = logging.getLogger(__name__)

# Состояния для создания бюджета
BUDGET_NAME, BUDGET_AMOUNT, BUDGET_CATEGORY, BUDGET_PERIOD = range(4)


async def budgets_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик меню бюджетов"""
    if update.message.text == "💰 Мои бюджеты":
        await update.message.reply_text(
            "💰 Управление бюджетами:",
            reply_markup=get_budget_keyboard()
        )


async def handle_budget_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback-запросов для бюджетов"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "budget_list":
        for session in get_session():
            try:
                service = BudgetService(session)
                budgets_data = service.get_user_budgets(user.id)
                
                if not budgets_data:
                    await query.edit_message_text(
                        "📊 У вас пока нет активных бюджетов.\n"
                        "Создайте свой первый бюджет для контроля расходов!"
                    )
                    return
                
                message = "💰 <b>Ваши активные бюджеты:</b>\n\n"
                
                for budget_info in budgets_data:
                    budget_message = service.format_budget_message(budget_info)
                    message += budget_message + "\n\n"
                
                await query.edit_message_text(message, parse_mode='HTML')
                
            except Exception as e:
                logger.error(f"Error getting budgets: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при получении бюджетов"
                )
    
    elif query.data == "budget_alerts":
        for session in get_session():
            try:
                service = BudgetService(session)
                alerts = service.check_budget_alerts(user.id)
                
                if not alerts:
                    await query.edit_message_text(
                        "✅ Отлично! Все бюджеты в норме.\n"
                        "Нет превышений или предупреждений."
                    )
                else:
                    message = "🔔 <b>Уведомления по бюджетам:</b>\n\n"
                    message += "\n\n".join(alerts)
                    await query.edit_message_text(message, parse_mode='HTML')
                    
            except Exception as e:
                logger.error(f"Error checking budget alerts: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при проверке уведомлений"
                )


async def start_budget_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало создания бюджета"""
    query = update.callback_query
    await query.answer()
    
    # Создаем специальную клавиатуру с уникальным паттерном
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
    ]
    cancel_keyboard = InlineKeyboardMarkup(keyboard)
    
    # Начинаем процесс создания бюджета
    await query.edit_message_text(
        "➕ <b>Создание нового бюджета</b>\n\n"
        "Введите название для вашего бюджета:\n"
        "(например: 'Продукты на февраль', 'Развлечения')",
        parse_mode='HTML',
        reply_markup=cancel_keyboard
    )
    return BUDGET_NAME


async def budget_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ввода названия бюджета"""
    budget_name = update.message.text.strip()
    
    if len(budget_name) < 2:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Название слишком короткое. Минимум 2 символа.\n"
            "Попробуйте еще раз:",
            reply_markup=cancel_keyboard
        )
        return BUDGET_NAME
    
    if len(budget_name) > 100:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Название слишком длинное. Максимум 100 символов.\n"
            "Попробуйте еще раз:",
            reply_markup=cancel_keyboard
        )
        return BUDGET_NAME
    
    # Сохраняем название в контексте
    context.user_data['budget_name'] = budget_name
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
    ]
    cancel_keyboard = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Название: <b>{budget_name}</b>\n\n"
        "💰 Теперь введите сумму бюджета в рублях:\n"
        "(например: 15000, 5000.50)",
        parse_mode='HTML',
        reply_markup=cancel_keyboard
    )
    
    return BUDGET_AMOUNT


async def budget_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ввода суммы бюджета"""
    amount_text = update.message.text.strip().replace(',', '.')
    
    try:
        amount = Decimal(amount_text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > Decimal('999999999.99'):
            raise ValueError("Сумма слишком большая")
    except (InvalidOperation, ValueError) as e:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Неверный формат суммы.\n"
            "Введите положительное число (например: 15000 или 5000.50):",
            reply_markup=cancel_keyboard
        )
        return BUDGET_AMOUNT
    
    # Сохраняем сумму в контексте
    context.user_data['budget_amount'] = amount
    
    # Получаем категории расходов пользователя
    user = update.effective_user
    for session in get_session():
        try:
            db_user = UserQueries.get_user_by_telegram_id(session, user.id)
            if not db_user:
                await update.message.reply_text("❌ Пользователь не найден")
                return ConversationHandler.END
            
            categories = CategoryQueries.get_user_categories(session, db_user.id)
            expense_categories = [cat.name for cat in categories if cat.transaction_type == TransactionType.EXPENSE]
            
            if not expense_categories:
                await update.message.reply_text(
                    "❌ У вас нет категорий расходов.\n"
                    "Сначала создайте транзакцию расхода, чтобы появились категории."
                )
                return ConversationHandler.END
            
            # Создаем клавиатуру категорий с кнопкой отмены
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = []
            
            for category in expense_categories:
                keyboard.append([
                    InlineKeyboardButton(category, callback_data=f"budget_cat_{category}")
                ])
            
            keyboard.append([
                InlineKeyboardButton("📝 Другая категория", callback_data="budget_cat_other")
            ])
            keyboard.append([
                InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")
            ])
            
            categories_keyboard = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Сумма: <b>{amount} ₽</b>\n\n"
                "📂 Выберите категорию для бюджета:",
                parse_mode='HTML',
                reply_markup=categories_keyboard
            )
            
            return BUDGET_CATEGORY
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
            ]
            cancel_keyboard = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Ошибка при получении категорий",
                reply_markup=cancel_keyboard
            )
            return BUDGET_AMOUNT


async def budget_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора категории бюджета"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("budget_cat_"):
        category_name = query.data.replace("budget_cat_", "")
        
        if category_name == "other":
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
            ]
            cancel_keyboard = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📝 Введите название новой категории:",
                reply_markup=cancel_keyboard
            )
            context.user_data['waiting_for_custom_category'] = True
            return BUDGET_CATEGORY
        
        # Сохраняем категорию в контексте
        context.user_data['budget_category'] = category_name
        
        # Предлагаем выбрать период
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("📅 Текущий месяц", callback_data="period_current_month")],
            [InlineKeyboardButton("📆 Следующий месяц", callback_data="period_next_month")],
            [InlineKeyboardButton("🗓️ Настроить период", callback_data="period_custom")],
            [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
        ]
        
        await query.edit_message_text(
            f"✅ Категория: <b>{category_name}</b>\n\n"
            "📅 Выберите период действия бюджета:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return BUDGET_PERIOD
    
    # Если ввод пользовательской категории
    if context.user_data.get('waiting_for_custom_category'):
        category_name = update.message.text.strip()
        
        if len(category_name) < 2:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
            ]
            cancel_keyboard = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Название категории слишком короткое. Минимум 2 символа.\n"
                "Попробуйте еще раз:",
                reply_markup=cancel_keyboard
            )
            return BUDGET_CATEGORY
        
        context.user_data['budget_category'] = category_name
        context.user_data['waiting_for_custom_category'] = False
        
        # Предлагаем выбрать период
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("📅 Текущий месяц", callback_data="period_current_month")],
            [InlineKeyboardButton("📆 Следующий месяц", callback_data="period_next_month")],
            [InlineKeyboardButton("🗓️ Настроить период", callback_data="period_custom")],
            [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
        ]
        
        await update.message.reply_text(
            f"✅ Категория: <b>{category_name}</b>\n\n"
            "📅 Выберите период действия бюджета:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return BUDGET_PERIOD


async def budget_period_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора периода бюджета"""
    query = update.callback_query
    await query.answer()
    
    now = datetime.now()
    
    if query.data == "period_current_month":
        # Текущий месяц
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_date = start_date.replace(year=now.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=now.month + 1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
    elif query.data == "period_next_month":
        # Следующий месяц
        if now.month == 12:
            start_date = datetime(now.year + 1, 1, 1)
            end_date = datetime(now.year + 1, 2, 1) - timedelta(days=1)
        else:
            start_date = datetime(now.year, now.month + 1, 1)
            if now.month == 11:
                end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(now.year, now.month + 2, 1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
    elif query.data == "period_custom":
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="budget_cancel")]
        ]
        cancel_keyboard = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗓️ Настройка пользовательского периода пока не реализована.\n"
            "Используйте готовые варианты выше.",
            reply_markup=cancel_keyboard
        )
        return BUDGET_PERIOD
    else:
        # Неизвестная команда
        return BUDGET_PERIOD
    
    # Создаем бюджет
    try:
        user = update.effective_user
        budget_name = context.user_data['budget_name']
        budget_amount = context.user_data['budget_amount']
        budget_category = context.user_data['budget_category']
        
        for session in get_session():
            service = BudgetService(session)
            budget = service.create_budget(
                telegram_id=user.id,
                name=budget_name,
                amount=budget_amount,
                category_name=budget_category,
                start_date=start_date,
                end_date=end_date
            )
            
            success_message = (
                "🎉 <b>Бюджет успешно создан!</b>\n\n"
                f"📝 Название: {budget.name}\n"
                f"💰 Сумма: {budget.amount} ₽\n"
                f"📂 Категория: {budget_category}\n"
                f"📅 Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n\n"
                "💡 Теперь ваши расходы в этой категории будут отслеживаться автоматически!"
            )
            
            await query.edit_message_text(success_message, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        await query.edit_message_text(f"❌ Ошибка при создании бюджета: {e}")
    
    # Очищаем данные из контекста
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_budget_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена создания бюджета"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Создание бюджета отменено")
    else:
        await update.message.reply_text("❌ Создание бюджета отменено")
    
    context.user_data.clear()
    return ConversationHandler.END


def setup_budget_handlers(app: Application) -> None:
    """Настройка обработчиков бюджетов"""
    
    # Обработчик меню бюджетов
    app.add_handler(MessageHandler(
        filters.Regex("^💰 Мои бюджеты$"),
        budgets_menu_handler
    ))
    
    # ConversationHandler для создания бюджетов
    budget_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            start_budget_creation,
            pattern="^budget_create$"
        )],
        states={
            BUDGET_NAME: [
                CallbackQueryHandler(cancel_budget_creation, pattern="^budget_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, budget_name_handler)
            ],
            BUDGET_AMOUNT: [
                CallbackQueryHandler(cancel_budget_creation, pattern="^budget_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, budget_amount_handler)
            ],
            BUDGET_CATEGORY: [
                CallbackQueryHandler(cancel_budget_creation, pattern="^budget_cancel$"),
                CallbackQueryHandler(budget_category_handler, pattern="^budget_cat_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, budget_category_handler)
            ],
            BUDGET_PERIOD: [
                CallbackQueryHandler(cancel_budget_creation, pattern="^budget_cancel$"),
                CallbackQueryHandler(budget_period_handler, pattern="^period_")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_budget_creation, pattern="^budget_cancel$"),
            MessageHandler(filters.COMMAND, cancel_budget_creation),
            MessageHandler(
                filters.Regex("^(➕ Добавить доход|➖ Добавить расход|📊 Мои транзакции|📈 Отчеты|⚙️ Настройки|ℹ️ Помощь)$"), 
                cancel_budget_creation
            )
        ],
        allow_reentry=True
    )
    
    app.add_handler(budget_conv_handler)
    
    # Остальные callback handlers для бюджетов
    app.add_handler(CallbackQueryHandler(
        handle_budget_callbacks,
        pattern=r"^budget_(list|alerts)$"
    )) 