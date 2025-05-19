#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Интеграция с Suno для бота поэзии
Отвечает за создание музыкальных треков на основе стихов
"""

import os
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

# Импортируем сервисы
from services.ai_service import AIService
from services.web_automation import WebAutomation


class SunoIntegration:
    """Класс для интеграции с Suno API"""
    
    def __init__(self):
        """Инициализация интеграции с Suno"""
        self.ai_service = AIService()
        self.web_automation = WebAutomation()
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_suno"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Получаем API ключ из переменных окружения (для API метода, если доступен)
        self.api_key = os.getenv("SUNO_API_KEY")
        self.api_url = "https://api.suno.ai/v1/tracks"
        
        # Флаг использования веб-интерфейса вместо API
        self.use_web_interface = True
        
        logger.info("Интеграция с Suno инициализирована")
    
    async def create_suno_prompt(self, poem: str, original_request: str) -> str:
        """Создание промпта для Suno на основе стихотворения
        
        Args:
            poem: Сгенерированное стихотворение
            original_request: Исходный запрос пользователя
            
        Returns:
            Промпт для Suno
        """
        try:
            # Формируем запрос к ИИ для создания промпта
            ai_prompt = f"""Создай музыкальный промпт для Suno AI на основе этого стихотворения:

{poem}

Исходный запрос пользователя: {original_request}

Промпт должен описывать стиль музыки, настроение, инструменты, темп и другие музыкальные характеристики.
Он должен быть кратким (до 100 слов) и вдохновляющим для создания музыки.
Не включай текст стихотворения в промпт, только музыкальное описание."""
            
            # Получаем промпт от ИИ
            suno_prompt = await self.ai_service.get_creative_response(ai_prompt)
            
            logger.info(f"Создан промпт для Suno: {suno_prompt[:50]}...")
            return suno_prompt
        
        except Exception as e:
            logger.error(f"Ошибка при создании промпта для Suno: {e}")
            return f"Create a musical track inspired by this poem about {original_request}. Use appropriate mood and style."
    
    async def create_track(self, prompt: str) -> Optional[str]:
        """Создание музыкального трека через Suno
        
        Args:
            prompt: Промпт для Suno
            
        Returns:
            URL созданного трека или None в случае ошибки
        """
        # Используем веб-интерфейс, если флаг установлен
        if self.use_web_interface:
            logger.info("Создание трека через веб-интерфейс Suno")
            track_url = await self.web_automation.create_suno_track(prompt)
            
            if track_url:
                return track_url
            else:
                logger.warning("Не удалось создать трек через веб-интерфейс. Пробуем API метод.")
        
        # Если веб-интерфейс не используется или произошла ошибка, пробуем API
        # Проверяем наличие API ключа
        if not self.api_key:
            logger.warning("API ключ Suno не найден. Используем заглушку.")
            return self._get_mock_track_url(prompt)
        
        try:
            # Заголовки запроса
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Данные запроса
            data = {
                "prompt": prompt,
                "model": "v3",  # Используем последнюю доступную модель
                "format": "mp3"
            }
            
            # Отправляем запрос к Suno API
            response = requests.post(self.api_url, headers=headers, json=data)
            
            # Проверяем ответ
            if response.status_code == 200:
                track_data = response.json()
                track_url = track_data.get("url")
                
                if track_url:
                    logger.info(f"Трек успешно создан через API: {track_url}")
                    return track_url
                else:
                    logger.error(f"Ошибка при получении URL трека: {track_data}")
            else:
                logger.error(f"Ошибка при создании трека через API: {response.status_code} - {response.text}")
            
            # В случае ошибки возвращаем заглушку
            return self._get_mock_track_url(prompt)
        
        except Exception as e:
            logger.error(f"Ошибка при взаимодействии с Suno API: {e}")
            return self._get_mock_track_url(prompt)
    
    def _get_mock_track_url(self, prompt: str) -> str:
        """Получение заглушки URL трека (для тестирования или при отсутствии API ключа)
        
        Args:
            prompt: Промпт для Suno
            
        Returns:
            Заглушка URL трека
        """
        # В реальном приложении здесь можно возвращать ссылку на демо-треки или другие альтернативы
        return "https://suno.ai/examples"
    
    def cleanup(self):
        """Очистка временных файлов и ресурсов"""
        try:
            # Закрываем браузер, если он был открыт
            if self.web_automation:
                import asyncio
                try:
                    asyncio.create_task(self.web_automation.close_browser())
                except Exception as e:
                    logger.error(f"Ошибка при закрытии браузера: {e}")
                
                # Очищаем ресурсы веб-автоматизации
                self.web_automation.cleanup()
            
            # Удаляем все временные файлы
            for file in self.temp_dir.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Ошибка при удалении временного файла {file}: {e}")
            
            # Удаляем временную директорию
            self.temp_dir.rmdir()
            logger.info("Временные файлы интеграции с Suno удалены")
        
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов интеграции с Suno: {e}")