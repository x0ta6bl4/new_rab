#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Генератор стихов для бота поэзии
Отвечает за создание креативных стихов с помощью ИИ
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger

# Импортируем сервис ИИ для генерации стихов
from services.ai_service import AIService


class PoetryGenerator:
    """Класс для генерации креативных стихов"""
    
    def __init__(self):
        """Инициализация генератора стихов"""
        self.ai_service = AIService()
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_poetry_generator"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Шаблоны для генерации стихов
        self.poetry_templates = [
            "Напиши креативное стихотворение на тему: {}",
            "Сочини оригинальный стих в стиле Маяковского о: {}",
            "Создай лирическое стихотворение, вдохновленное: {}",
            "Напиши стихотворение с рифмой и ритмом о: {}",
            "Сочини короткое, но глубокое стихотворение о: {}"
        ]
        
        logger.info("Генератор стихов инициализирован")
    
    async def generate_poem(self, prompt: str) -> str:
        """Генерация стихотворения на основе запроса
        
        Args:
            prompt: Запрос или тема для стихотворения
            
        Returns:
            Сгенерированное стихотворение
        """
        try:
            # Очищаем запрос от лишних слов
            clean_prompt = self._clean_prompt(prompt)
            
            # Выбираем шаблон для генерации
            template = self._select_template(clean_prompt)
            
            # Формируем полный запрос к ИИ
            full_prompt = template.format(clean_prompt)
            
            # Добавляем инструкции для ИИ
            full_prompt += "\n\nСтихотворение должно быть оригинальным, креативным, с хорошей рифмой и ритмом. "
            full_prompt += "Используй яркие образы и метафоры. Длина - 8-16 строк."
            
            # Получаем стихотворение от ИИ
            poem = await self.ai_service.get_creative_response(full_prompt)
            
            # Форматируем результат
            formatted_poem = self._format_poem(poem)
            
            logger.info(f"Сгенерировано стихотворение на тему: {clean_prompt[:30]}...")
            return formatted_poem
        
        except Exception as e:
            logger.error(f"Ошибка при генерации стихотворения: {e}")
            return "Не удалось создать стихотворение. Попробуйте другую тему."
    
    def _clean_prompt(self, prompt: str) -> str:
        """Очистка запроса от лишних слов и фраз
        
        Args:
            prompt: Исходный запрос
            
        Returns:
            Очищенный запрос
        """
        # Удаляем фразы типа "напиши стих о", "сочини стихотворение про" и т.д.
        phrases_to_remove = [
            "напиши стих", "напиши стихотворение", "сочини стих", "сочини стихотворение",
            "создай стих", "создай стихотворение", "придумай стих", "придумай стихотворение",
            "поэт,", "@поэт", "стихотворение о", "стихотворение про", "стих о", "стих про"
        ]
        
        result = prompt.lower()
        for phrase in phrases_to_remove:
            result = result.replace(phrase, "")
        
        # Удаляем лишние пробелы и знаки препинания в начале и конце
        result = result.strip(" ,.!?:;-")
        
        return result if result else "вдохновение"
    
    def _select_template(self, prompt: str) -> str:
        """Выбор шаблона для генерации стихотворения
        
        Args:
            prompt: Очищенный запрос
            
        Returns:
            Шаблон для генерации
        """
        # Простой алгоритм выбора шаблона на основе длины запроса
        # В реальном приложении можно использовать более сложную логику
        index = hash(prompt) % len(self.poetry_templates)
        return self.poetry_templates[index]
    
    def _format_poem(self, poem: str) -> str:
        """Форматирование сгенерированного стихотворения
        
        Args:
            poem: Сгенерированное стихотворение
            
        Returns:
            Отформатированное стихотворение
        """
        # Удаляем лишние кавычки, если они есть
        poem = poem.strip('"\' ')
        
        # Удаляем лишние пробелы и переносы строк
        lines = [line.strip() for line in poem.split('\n')]
        
        # Удаляем пустые строки
        lines = [line for line in lines if line]
        
        # Собираем стихотворение обратно
        formatted_poem = '\n'.join(lines)
        
        return formatted_poem
    
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
            logger.info("Временные файлы генератора стихов удалены")
        
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов генератора стихов: {e}")