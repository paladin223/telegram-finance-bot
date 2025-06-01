"""
Клавиатуры для Telegram бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура"""
    keyboard = [
        [KeyboardButton("➕ Добавить доход"), KeyboardButton("➖ Добавить расход")],
        [KeyboardButton("📊 Мои транзакции"), KeyboardButton("💰 Мои бюджеты")],
        [KeyboardButton("📈 Отчеты"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_transaction_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа транзакции"""
    keyboard = [
        [InlineKeyboardButton("💰 Доход", callback_data="transaction_type_income")],
        [InlineKeyboardButton("💸 Расход", callback_data="transaction_type_expense")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_reports_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отчетов"""
    keyboard = [
        [InlineKeyboardButton("📊 Месячный отчет", callback_data="report_monthly")],
        [InlineKeyboardButton("📅 Недельный отчет", callback_data="report_weekly")],
        [InlineKeyboardButton("📋 Мои отчеты", callback_data="report_list")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_budget_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура бюджетов"""
    keyboard = [
        [InlineKeyboardButton("➕ Создать бюджет", callback_data="budget_create")],
        [InlineKeyboardButton("📊 Мои бюджеты", callback_data="budget_list")],
        [InlineKeyboardButton("🔔 Проверить уведомления", callback_data="budget_alerts")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_categories_keyboard(categories: List[str], prefix: str = "category") -> InlineKeyboardMarkup:
    """Клавиатура выбора категорий"""
    keyboard = []
    
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(category, callback_data=f"{prefix}_{category}")
        ])
    
    # Добавляем кнопку "Другая категория"
    keyboard.append([
        InlineKeyboardButton("📝 Другая категория", callback_data=f"{prefix}_other")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_yes")],
        [InlineKeyboardButton("❌ Нет", callback_data=f"confirm_{action}_no")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    keyboard = [
        [InlineKeyboardButton("📂 Управление категориями", callback_data="settings_categories")],
        [InlineKeyboardButton("🔔 Настройки уведомлений", callback_data="settings_notifications")],
        [InlineKeyboardButton("🗑️ Очистить данные", callback_data="settings_clear_data")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены"""
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    
    return InlineKeyboardMarkup(keyboard) 