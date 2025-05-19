#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Многоботовая система для Telegram
Главный файл проекта, который инициализирует и запускает всю систему
"""

import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from loguru import logger

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загрузка переменных окружения из файла keys.env
env_path = Path(__file__).parent.parent / 'keys.env'
load_dotenv(dotenv_path=env_path)

# Получение токена Telegram из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("Не найден токен Telegram. Убедитесь, что файл keys.env содержит TELEGRAM_BOT_TOKEN.")
    exit(1)

# Импорт компонентов системы
try:
    from core.bot_manager import BotManager
    from bots.main_bot.main_bot import MainBot
    from bots.poetry_bot.poetry_bot import PoetryBot
    from core.database import init_db
except ImportError as e:
    logger.error(f"Ошибка импорта компонентов: {e}")
    exit(1)


def setup_database():
    """Инициализация базы данных"""
    try:
        init_db()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        exit(1)


def main():
    """Основная функция запуска многоботовой системы"""
    logger.info("Запуск многоботовой системы для Telegram...")
    
    # Инициализация базы данных
    setup_database()
    
    # Создание экземпляра менеджера ботов
    bot_manager = BotManager(telegram_token=TELEGRAM_TOKEN)
    
    # Регистрация ботов в системе
    main_bot = MainBot(name="main_bot", description="Главный бот для обработки голосовых сообщений")
    poetry_bot = PoetryBot(name="poetry_bot", description="Бот для создания креативных стихов и музыки")
    
    # Добавление ботов в менеджер
    bot_manager.register_bot(main_bot)
    bot_manager.register_bot(poetry_bot)
    
    # Запуск системы
    try:
        logger.info("Система запущена и готова к работе!")
        bot_manager.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения работы...")
    except Exception as e:
        logger.error(f"Произошла ошибка при работе системы: {e}")
    finally:
        # Корректное завершение работы
        bot_manager.stop()
        logger.info("Система остановлена")


if __name__ == "__main__":
    main()