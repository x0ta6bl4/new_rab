#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Генератор голосовых ответов для главного бота
Отвечает за преобразование текста в голосовые сообщения
"""

import os
import tempfile
from pathlib import Path
import asyncio
from typing import Optional
from loguru import logger

# Используем edge-tts как бесплатную альтернативу для генерации голоса
import edge_tts


class TTSGenerator:
    """Класс для генерации голосовых ответов из текста"""
    
    def __init__(self):
        """Инициализация генератора голосовых ответов"""
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Настройки голоса (русский женский голос)
        self.voice = "ru-RU-SvetlanaNeural"
        logger.info("Генератор голосовых ответов инициализирован")
    
    async def text_to_speech(self, text: str, output_path: Path) -> bool:
        """Преобразование текста в голосовое сообщение
        
        Args:
            text: Текст для преобразования
            output_path: Путь для сохранения голосового файла
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            # Создаем коммуникатор для edge-tts
            communicate = edge_tts.Communicate(text, self.voice)
            
            # Преобразуем текст в речь и сохраняем в файл
            await communicate.save(str(output_path))
            
            logger.info(f"Голосовое сообщение успешно создано: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при создании голосового сообщения: {e}")
            return False
    
    def set_voice(self, voice: str):
        """Установка голоса для генерации
        
        Args:
            voice: Идентификатор голоса
        """
        self.voice = voice
        logger.info(f"Установлен голос: {voice}")
    
    async def get_available_voices(self):
        """Получение списка доступных голосов
        
        Returns:
            Список доступных голосов
        """
        try:
            # Получаем список доступных голосов
            voices = await edge_tts.list_voices()
            return voices
        except Exception as e:
            logger.error(f"Ошибка при получении списка голосов: {e}")
            return []
    
    def cleanup(self):
        """Очистка временных файлов и ресурсов"""
        try:
            # Удаляем все временные файлы
            for file in self.temp_dir.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Ошибка при удалении временного файла {file}: {e}")
            
            # Удаляем временную директорию
            self.temp_dir.rmdir()
            logger.info("Временные файлы генератора голосовых ответов удалены")
        
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов генератора голосовых ответов: {e}")