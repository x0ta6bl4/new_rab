#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Базовый класс бота для многоботовой системы Telegram
Определяет общий интерфейс для всех ботов в системе
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from telegram import File
from telegram.ext import ContextTypes
from loguru import logger


class BaseBot(ABC):
    """Абстрактный базовый класс для всех ботов в системе"""
    
    def __init__(self, name: str, description: str = ""):
        """Инициализация базового бота
        
        Args:
            name: Уникальное имя бота
            description: Описание функциональности бота
        """
        self.name = name
        self.description = description
        self.manager = None
        self.is_initialized = False
        logger.info(f"Бот {name} создан")
    
    def set_manager(self, manager):
        """Установка менеджера ботов
        
        Args:
            manager: Экземпляр менеджера ботов
        """
        self.manager = manager
        logger.debug(f"Бот {self.name} привязан к менеджеру")
    
    def initialize(self):
        """Инициализация бота перед запуском"""
        if self.is_initialized:
            logger.warning(f"Бот {self.name} уже инициализирован")
            return
        
        self._initialize_bot()
        self.is_initialized = True
        logger.info(f"Бот {self.name} инициализирован")
    
    def shutdown(self):
        """Корректное завершение работы бота"""
        if not self.is_initialized:
            logger.warning(f"Бот {self.name} не был инициализирован")
            return
        
        self._shutdown_bot()
        self.is_initialized = False
        logger.info(f"Бот {self.name} остановлен")
    
    @abstractmethod
    async def process_text(self, user_id: int, text: str, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Обработка текстового сообщения
        
        Args:
            user_id: ID пользователя
            text: Текст сообщения
            context: Контекст Telegram
            
        Returns:
            Ответ на сообщение или None, если ответ не требуется
        """
        pass
    
    @abstractmethod
    async def process_voice(self, user_id: int, voice_file: File, context: ContextTypes.DEFAULT_TYPE) -> Union[str, Dict[str, Any], None]:
        """Обработка голосового сообщения
        
        Args:
            user_id: ID пользователя
            voice_file: Объект голосового файла
            context: Контекст Telegram
            
        Returns:
            Ответ на сообщение (текст, путь к голосовому файлу или None)
        """
        pass
    
    @abstractmethod
    def _initialize_bot(self):
        """Внутренний метод инициализации бота"""
        pass
    
    @abstractmethod
    def _shutdown_bot(self):
        """Внутренний метод завершения работы бота"""
        pass
    
    def __str__(self):
        return f"Bot(name={self.name}, description={self.description})"
    
    def __repr__(self):
        return self.__str__()