"""
Обработчики для работы с отчетами
"""

import logging
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

from app.database import get_session
from app.services.report_service import ReportService
from app.bot.keyboards import get_reports_keyboard

logger = logging.getLogger(__name__)


async def reports_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик меню отчетов"""
    if update.message.text == "📈 Отчеты":
        await update.message.reply_text(
            "📈 Генерация отчетов:",
            reply_markup=get_reports_keyboard()
        )


async def handle_report_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback-запросов для отчетов"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "report_monthly":
        for session in get_session():
            try:
                service = ReportService(session)
                report = service.generate_monthly_report(user.id)
                
                await query.edit_message_text(
                    f"📊 <b>Месячный отчет</b>\n\n{report}",
                    parse_mode='HTML'
                )
                
            except Exception as e:
                logger.error(f"Error generating monthly report: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при создании отчета"
                )
    
    elif query.data == "report_weekly":
        for session in get_session():
            try:
                service = ReportService(session)
                report = service.generate_weekly_report(user.id)
                
                await query.edit_message_text(
                    f"📈 <b>Недельный отчет</b>\n\n{report}",
                    parse_mode='HTML'
                )
                
            except Exception as e:
                logger.error(f"Error generating weekly report: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при создании отчета"
                )
    
    elif query.data == "report_categories":
        for session in get_session():
            try:
                service = ReportService(session)
                report = service.generate_categories_report(user.id)
                
                await query.edit_message_text(
                    f"📊 <b>Отчет по категориям</b>\n\n{report}",
                    parse_mode='HTML'
                )
                
            except Exception as e:
                logger.error(f"Error generating categories report: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при создании отчета"
                )
    
    elif query.data == "report_history":
        await query.edit_message_text(
            "📚 История отчетов\n\n"
            "Функция просмотра сохраненных отчетов находится в разработке.\n"
            "Скоро будет доступна!"
        )


def setup_report_handlers(app: Application) -> None:
    """Настройка обработчиков отчетов"""
    
    # Обработчик меню отчетов
    app.add_handler(MessageHandler(
        filters.Regex("^📈 Отчеты$"),
        reports_menu_handler
    ))
    
    # Callback handlers для отчетов
    app.add_handler(CallbackQueryHandler(
        handle_report_callbacks,
        pattern=r"^report_"
    )) 