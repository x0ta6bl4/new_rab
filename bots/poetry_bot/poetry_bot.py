#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Бот для создания креативных стихов и музыки
Отвечает за генерацию стихов и интеграцию с Suno для создания музыкальных треков
"""

import os
import tempfile
from typing import Optional, Dict, Any, Union
from pathlib import Path
from telegram import File
from telegram.ext import ContextTypes
from loguru import logger

from bots.base_bot import BaseBot
from bots.poetry_bot.poetry_generator import PoetryGenerator
from bots.poetry_bot.suno_integration import SunoIntegration
from services.ai_service import AIService


class PoetryBot(BaseBot):
    """Бот для создания креативных стихов и музыки"""
    
    def __init__(self, name: str, description: str = ""):
        """Инициализация бота для стихов
        
        Args:
            name: Уникальное имя бота
            description: Описание функциональности бота
        """
        super().__init__(name, description)
        self.poetry_generator = None
        self.suno_integration = None
        self.ai_service = None
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_poetry"
        self.temp_dir.mkdir(exist_ok=True)
    
    def _initialize_bot(self):
        """Инициализация компонентов бота"""
        # Инициализация генератора стихов
        self.poetry_generator = PoetryGenerator()
        
        # Инициализация интеграции с Suno
        self.suno_integration = SunoIntegration()
        
        # Инициализация сервиса ИИ
        self.ai_service = AIService()
        
        logger.info(f"Бот для стихов {self.name} инициализирован")
    
    def _shutdown_bot(self):
        """Завершение работы бота"""
        # Освобождение ресурсов
        if self.poetry_generator:
            self.poetry_generator.cleanup()
        
        if self.suno_integration:
            self.suno_integration.cleanup()
        
        if self.ai_service:
            self.ai_service.cleanup()
        
        # Удаление временных файлов
        for file in self.temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла {file}: {e}")
        
        logger.info(f"Бот для стихов {self.name} остановлен")
    
    async def process_text(self, user_id: int, text: str, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Обработка текстового сообщения
        
        Args:
            user_id: ID пользователя
            text: Текст сообщения
            context: Контекст Telegram
            
        Returns:
            Ответ на сообщение или None, если ответ не требуется
        """
        logger.info(f"Обработка запроса на создание стиха от пользователя {user_id}: {text[:50]}...")
        
        try:
            # Проверяем, содержит ли сообщение запрос на создание музыки
            if any(keyword in text.lower() for keyword in ["музык", "песн", "трек", "мелоди", "suno"]):
                # Отправляем уведомление о начале обработки
                await context.bot.send_message(
                    chat_id=user_id,
                    text="Начинаю создание стиха и музыкального трека. Это может занять некоторое время..."
                )
                
                # Генерируем стих
                poem = await self.poetry_generator.generate_poem(text)
                
                # Создаем промпт для Suno
                suno_prompt = await self.suno_integration.create_suno_prompt(poem, text)
                
                # Отправляем промпт в Suno и получаем ссылку на трек
                track_url = await self.suno_integration.create_track(suno_prompt)
                
                if track_url:
                    return f"Вот стих, который я сочинил:\n\n{poem}\n\nА вот музыкальный трек на его основе: {track_url}"
                else:
                    return f"Вот стих, который я сочинил:\n\n{poem}\n\nК сожалению, не удалось создать музыкальный трек. Попробуйте позже."
            else:
                # Просто генерируем стих
                poem = await self.poetry_generator.generate_poem(text)
                return f"Вот стих, который я сочинил:\n\n{poem}"
        
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса на создание стиха: {e}")
            return "Извините, произошла ошибка при создании стиха. Попробуйте позже."
    
    async def process_voice(self, user_id: int, voice_file: File, context: ContextTypes.DEFAULT_TYPE) -> Union[str, Dict[str, Any], None]:
        """Обработка голосового сообщения
        
        Args:
            user_id: ID пользователя
            voice_file: Объект голосового файла
            context: Контекст Telegram
            
        Returns:
            Ответ на сообщение (текст, путь к голосовому файлу или None)
        """
        # Бот для стихов не обрабатывает голосовые сообщения напрямую
        # Перенаправляем обработку главному боту через менеджера
        if self.manager:
            main_bot = self.manager.get_bot("main_bot")
            if main_bot:
                return await main_bot.process_voice(user_id, voice_file, context)
        
        return "Извините, я не могу обрабатывать голосовые сообщения. Пожалуйста, отправьте текстовый запрос."