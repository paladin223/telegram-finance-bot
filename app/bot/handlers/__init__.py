"""
Handlers package для обработчиков бота
"""

from telegram.ext import Application
from .main import setup_main_handlers
from .transactions import setup_transaction_handlers
from .budgets import setup_budget_handlers
from .reports import setup_report_handlers


def setup_handlers(app: Application) -> None:
    """Настройка всех обработчиков"""
    # Сначала добавляем специфические обработчики
    setup_transaction_handlers(app)
    setup_budget_handlers(app)
    setup_report_handlers(app)
    
    # Потом общие обработчики (которые должны быть последними)
    setup_main_handlers(app) 