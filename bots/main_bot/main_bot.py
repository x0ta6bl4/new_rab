#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Главный бот для многоботовой системы Telegram
Отвечает за обработку голосовых сообщений и генерацию голосовых ответов
"""

import os
import tempfile
from typing import Optional, Dict, Any, Union
from pathlib import Path
from telegram import File
from telegram.ext import ContextTypes
from loguru import logger

from bots.base_bot import BaseBot
from bots.main_bot.voice_handler import VoiceHandler
from bots.main_bot.tts_generator import TTSGenerator
from services.ai_service import AIService


class MainBot(BaseBot):
    """Главный бот для обработки голосовых сообщений и координации работы системы"""
    
    def __init__(self, name: str, description: str = ""):
        """Инициализация главного бота
        
        Args:
            name: Уникальное имя бота
            description: Описание функциональности бота
        """
        super().__init__(name, description)
        self.voice_handler = None
        self.tts_generator = None
        self.ai_service = None
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_voice"
        self.temp_dir.mkdir(exist_ok=True)
    
    def _initialize_bot(self):
        """Инициализация компонентов бота"""
        # Инициализация обработчика голосовых сообщений
        self.voice_handler = VoiceHandler()
        
        # Инициализация генератора голосовых ответов
        self.tts_generator = TTSGenerator()
        
        # Инициализация сервиса ИИ
        self.ai_service = AIService()
        
        logger.info(f"Главный бот {self.name} инициализирован")
    
    def _shutdown_bot(self):
        """Завершение работы бота"""
        # Освобождение ресурсов
        if self.voice_handler:
            self.voice_handler.cleanup()
        
        if self.tts_generator:
            self.tts_generator.cleanup()
        
        if self.ai_service:
            self.ai_service.cleanup()
        
        # Удаление временных файлов
        for file in self.temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла {file}: {e}")
        
        logger.info(f"Главный бот {self.name} остановлен")
    
    async def process_text(self, user_id: int, text: str, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Обработка текстового сообщения
        
        Args:
            user_id: ID пользователя
            text: Текст сообщения
            context: Контекст Telegram
            
        Returns:
            Ответ на сообщение или None, если ответ не требуется
        """
        logger.info(f"Обработка текстового сообщения от пользователя {user_id}: {text[:50]}...")
        
        try:
            # Получение ответа от ИИ
            response = await self.ai_service.get_text_response(user_id, text)
            return response
        except Exception as e:
            logger.error(f"Ошибка при обработке текстового сообщения: {e}")
            return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже."
    
    async def process_voice(self, user_id: int, voice_file: File, context: ContextTypes.DEFAULT_TYPE) -> Union[str, Dict[str, Any], None]:
        """Обработка голосового сообщения
        
        Args:
            user_id: ID пользователя
            voice_file: Объект голосового файла
            context: Контекст Telegram
            
        Returns:
            Ответ на сообщение (текст, путь к голосовому файлу или None)
        """
        logger.info(f"Обработка голосового сообщения от пользователя {user_id}")
        
        try:
            # Создаем временный файл для сохранения голосового сообщения
            voice_path = self.temp_dir / f"voice_{user_id}_{voice_file.file_unique_id}.ogg"
            await voice_file.download_to_drive(voice_path)
            
            # Преобразуем голосовое сообщение в текст
            text = await self.voice_handler.speech_to_text(voice_path)
            if not text:
                return "Извините, не удалось распознать голосовое сообщение. Попробуйте еще раз."
            
            # Получаем ответ от ИИ
            response_text = await self.ai_service.get_text_response(user_id, text)
            
            # Преобразуем ответ в голосовое сообщение
            response_voice_path = self.temp_dir / f"response_{user_id}_{voice_file.file_unique_id}.ogg"
            success = await self.tts_generator.text_to_speech(response_text, response_voice_path)
            
            if success:
                # Возвращаем путь к голосовому файлу
                return {"voice_path": str(response_voice_path), "text": response_text}
            else:
                # Если не удалось создать голосовое сообщение, возвращаем текст
                return f"Распознанный текст: {text}\n\nОтвет: {response_text}\n\n(Не удалось создать голосовое сообщение)"
        
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            return "Извините, произошла ошибка при обработке вашего голосового сообщения. Попробуйте позже."
    
    async def generate_voice_response(self, text: str, user_id: int) -> Optional[str]:
        """Генерация голосового ответа из текста
        
        Args:
            text: Текст для преобразования в голос
            user_id: ID пользователя
            
        Returns:
            Путь к файлу с голосовым ответом или None в случае ошибки
        """
        try:
            # Создаем временный файл для голосового ответа
            voice_path = self.temp_dir / f"generated_voice_{user_id}_{hash(text)}.ogg"
            
            # Преобразуем текст в голос
            success = await self.tts_generator.text_to_speech(text, voice_path)
            
            if success:
                return str(voice_path)
            else:
                logger.error("Не удалось создать голосовое сообщение")
                return None
        
        except Exception as e:
            logger.error(f"Ошибка при генерации голосового ответа: {e}")
            return None