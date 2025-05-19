#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Менеджер ботов для многоботовой системы Telegram
Отвечает за инициализацию, регистрацию и координацию всех ботов
"""

import asyncio
from typing import Dict, List, Optional, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger

from bots.base_bot import BaseBot
from core.message_router import MessageRouter


class BotManager:
    """Класс для управления всеми ботами в системе"""
    
    def __init__(self, telegram_token: str):
        """Инициализация менеджера ботов
        
        Args:
            telegram_token: Токен Telegram бота
        """
        self.telegram_token = telegram_token
        self.application = Application.builder().token(telegram_token).build()
        self.bots: Dict[str, BaseBot] = {}
        self.message_router = MessageRouter()
        self.is_running = False
        
        # Регистрация базовых обработчиков
        self._register_handlers()
        
        logger.info("Менеджер ботов инициализирован")
    
    def _register_handlers(self):
        """Регистрация базовых обработчиков команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self._start_command))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self._help_command))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
        
        # Обработчик голосовых сообщений
        self.application.add_handler(MessageHandler(filters.VOICE, self._handle_voice))
        
        # Обработчик ошибок
        self.application.add_error_handler(self._error_handler)
        
        logger.info("Базовые обработчики зарегистрированы")
    
    def register_bot(self, bot: BaseBot):
        """Регистрация нового бота в системе
        
        Args:
            bot: Экземпляр бота для регистрации
        """
        if bot.name in self.bots:
            logger.warning(f"Бот с именем {bot.name} уже зарегистрирован. Перезаписываем.")
        
        self.bots[bot.name] = bot
        bot.set_manager(self)
        logger.info(f"Бот {bot.name} успешно зарегистрирован")
    
    def get_bot(self, name: str) -> Optional[BaseBot]:
        """Получение бота по имени
        
        Args:
            name: Имя бота
            
        Returns:
            Экземпляр бота или None, если бот не найден
        """
        return self.bots.get(name)
    
    def get_all_bots(self) -> List[BaseBot]:
        """Получение списка всех зарегистрированных ботов
        
        Returns:
            Список всех ботов
        """
        return list(self.bots.values())
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            f"Я многофункциональный бот с несколькими помощниками.\n"
            f"Используй /help для получения списка доступных команд."
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = "Доступные команды и функции:\n\n"
        help_text += "/start - Начать общение с ботом\n"
        help_text += "/help - Показать это сообщение\n\n"
        
        # Добавляем информацию о каждом зарегистрированном боте
        help_text += "Доступные боты:\n"
        for bot in self.bots.values():
            help_text += f"- {bot.name}: {bot.description}\n"
        
        await update.message.reply_text(help_text)
    
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Определяем, какой бот должен обработать сообщение
        target_bot = self.message_router.route_text_message(message_text, self.bots)
        
        if target_bot:
            # Передаем сообщение соответствующему боту
            response = await target_bot.process_text(user_id, message_text, context)
            if response:
                await update.message.reply_text(response)
        else:
            # Если не определен конкретный бот, используем главного бота
            main_bot = self.get_bot("main_bot")
            if main_bot:
                response = await main_bot.process_text(user_id, message_text, context)
                if response:
                    await update.message.reply_text(response)
            else:
                await update.message.reply_text(
                    "Извините, я не могу обработать ваше сообщение. Попробуйте другой запрос."
                )
    
    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик голосовых сообщений"""
        user_id = update.effective_user.id
        voice_file = await update.message.voice.get_file()
        
        # Голосовые сообщения всегда обрабатываются главным ботом
        main_bot = self.get_bot("main_bot")
        if main_bot:
            # Отправляем уведомление о начале обработки
            processing_message = await update.message.reply_text("Обрабатываю голосовое сообщение...")
            
            # Обрабатываем голосовое сообщение
            response = await main_bot.process_voice(user_id, voice_file, context)
            
            # Удаляем сообщение о обработке
            await processing_message.delete()
            
            # Отправляем ответ
            if isinstance(response, str):
                await update.message.reply_text(response)
            elif isinstance(response, dict) and 'voice_path' in response:
                # Если ответ содержит путь к голосовому файлу, отправляем его
                with open(response['voice_path'], 'rb') as voice:
                    await update.message.reply_voice(voice)
            else:
                await update.message.reply_text(
                    "Извините, произошла ошибка при обработке голосового сообщения."
                )
        else:
            await update.message.reply_text(
                "Извините, обработка голосовых сообщений временно недоступна."
            )
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Произошла ошибка: {context.error} при обработке {update}")
        if update:
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."
            )
    
    def start(self):
        """Запуск менеджера ботов"""
        if self.is_running:
            logger.warning("Менеджер ботов уже запущен")
            return
        
        # Инициализация всех ботов
        for bot in self.bots.values():
            bot.initialize()
        
        # Запуск приложения
        self.is_running = True
        self.application.run_polling()
    
    def stop(self):
        """Остановка менеджера ботов"""
        if not self.is_running:
            logger.warning("Менеджер ботов не запущен")
            return
        
        # Остановка всех ботов
        for bot in self.bots.values():
            bot.shutdown()
        
        # Остановка приложения
        self.is_running = False
        if self.application.running:
            self.application.stop()
        
        logger.info("Менеджер ботов остановлен")