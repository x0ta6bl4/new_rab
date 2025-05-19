#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Маршрутизатор сообщений для многоботовой системы Telegram
Определяет, какой бот должен обрабатывать конкретное сообщение
"""

import re
from typing import Dict, Optional, List
from loguru import logger


class MessageRouter:
    """Класс для маршрутизации сообщений между ботами"""
    
    def __init__(self):
        """Инициализация маршрутизатора сообщений"""
        # Ключевые слова и фразы для определения бота
        self.poetry_keywords = [
            r"стих", r"поэм", r"рифм", r"строф", r"сочини", r"напиши стих", 
            r"музык", r"песн", r"трек", r"мелоди", r"suno"
        ]
        
        # Шаблоны для прямого обращения к ботам
        self.direct_patterns = {
            "main_bot": re.compile(r"^@?главный\s+бот[,:].+", re.IGNORECASE | re.DOTALL),
            "poetry_bot": re.compile(r"^@?поэт[,:].+", re.IGNORECASE | re.DOTALL)
        }
        
        logger.info("Маршрутизатор сообщений инициализирован")
    
    def route_text_message(self, text: str, bots: Dict[str, any]) -> Optional[any]:
        """Определяет, какой бот должен обработать текстовое сообщение
        
        Args:
            text: Текст сообщения
            bots: Словарь доступных ботов
            
        Returns:
            Экземпляр бота, который должен обработать сообщение, или None
        """
        # Проверяем прямое обращение к ботам
        for bot_name, pattern in self.direct_patterns.items():
            if pattern.match(text) and bot_name in bots:
                logger.debug(f"Сообщение направлено напрямую боту {bot_name}")
                return bots[bot_name]
        
        # Проверяем ключевые слова для бота стихов
        if any(re.search(keyword, text, re.IGNORECASE) for keyword in self.poetry_keywords):
            if "poetry_bot" in bots:
                logger.debug("Сообщение содержит ключевые слова для бота стихов")
                return bots["poetry_bot"]
        
        # По умолчанию используем главного бота
        if "main_bot" in bots:
            logger.debug("Сообщение будет обработано главным ботом")
            return bots["main_bot"]
        
        # Если главный бот не найден, возвращаем первый доступный бот
        if bots:
            first_bot = list(bots.values())[0]
            logger.debug(f"Главный бот не найден, используем {first_bot.name}")
            return first_bot
        
        logger.warning("Нет доступных ботов для обработки сообщения")
        return None