#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Сервис ИИ для многоботовой системы Telegram
Предоставляет интерфейс для взаимодействия с различными ИИ-моделями
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger

# Для локальных моделей (бесплатный вариант)
try:
    from huggingface_hub import hf_hub_download
    from transformers import pipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("Библиотеки Hugging Face не установлены. Будет использована заглушка.")

# Для локальных LLM моделей (бесплатный вариант)
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    logger.warning("Библиотека llama-cpp-python не установлена. Будет использована заглушка.")


class AIService:
    """Сервис для взаимодействия с ИИ-моделями"""
    
    def __init__(self):
        """Инициализация сервиса ИИ"""
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_ai"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Получаем API ключи из переменных окружения
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Инициализируем модели
        self.text_model = None
        self.creative_model = None
        
        # Инициализируем кэш ответов
        self.response_cache = {}
        
        logger.info("Сервис ИИ инициализирован")
        
        # Загружаем модели при инициализации
        self._initialize_models()
    
    def _initialize_models(self):
        """Инициализация ИИ-моделей"""
        # Если доступен OpenAI API ключ, используем его
        if self.openai_api_key:
            logger.info("Найден API ключ OpenAI. Будет использоваться OpenAI API.")
            return
        
        # Если доступны библиотеки Hugging Face, используем локальные модели
        if HF_AVAILABLE:
            try:
                # Инициализируем модель для обычных ответов
                logger.info("Инициализация локальной модели для обычных ответов...")
                self.text_model = pipeline(
                    "text-generation",
                    model="IlyaGusev/saiga_mistral_7b_gguf",  # Русскоязычная модель
                    trust_remote_code=True
                )
                
                # Инициализируем модель для креативных ответов
                logger.info("Инициализация локальной модели для креативных ответов...")
                self.creative_model = self.text_model  # Используем ту же модель
                
                logger.info("Локальные модели успешно инициализированы")
            except Exception as e:
                logger.error(f"Ошибка при инициализации локальных моделей: {e}")
        
        # Если доступна библиотека llama-cpp-python, используем локальную LLM модель
        elif LLAMA_AVAILABLE:
            try:
                # Загружаем модель из Hugging Face Hub
                logger.info("Загрузка локальной LLM модели...")
                model_path = hf_hub_download(
                    repo_id="IlyaGusev/saiga_mistral_7b_gguf",
                    filename="model-q4_K.gguf",
                    cache_dir=str(self.temp_dir)
                )
                
                # Инициализируем модель
                self.text_model = Llama(
                    model_path=model_path,
                    n_ctx=2048,  # Размер контекста
                    n_threads=4   # Количество потоков
                )
                
                self.creative_model = self.text_model  # Используем ту же модель
                
                logger.info("Локальная LLM модель успешно инициализирована")
            except Exception as e:
                logger.error(f"Ошибка при инициализации локальной LLM модели: {e}")
    
    async def get_text_response(self, user_id: int, text: str) -> str:
        """Получение текстового ответа от ИИ
        
        Args:
            user_id: ID пользователя
            text: Текст запроса
            
        Returns:
            Ответ от ИИ
        """
        # Создаем ключ для кэша
        cache_key = f"text_{hash(text)}"
        
        # Проверяем кэш
        if cache_key in self.response_cache:
            logger.debug(f"Ответ найден в кэше: {cache_key}")
            return self.response_cache[cache_key]
        
        try:
            # Если доступен OpenAI API ключ, используем его
            if self.openai_api_key:
                response = await self._get_openai_response(text)
            # Если доступна локальная модель, используем ее
            elif self.text_model:
                response = await self._get_local_model_response(text, self.text_model)
            # Иначе используем заглушку
            else:
                response = self._get_mock_response(text)
            
            # Сохраняем ответ в кэш
            self.response_cache[cache_key] = response
            
            return response
        
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от ИИ: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."
    
    async def get_creative_response(self, prompt: str) -> str:
        """Получение креативного ответа от ИИ
        
        Args:
            prompt: Текст запроса
            
        Returns:
            Креативный ответ от ИИ
        """
        # Создаем ключ для кэша
        cache_key = f"creative_{hash(prompt)}"
        
        # Проверяем кэш
        if cache_key in self.response_cache:
            logger.debug(f"Креативный ответ найден в кэше: {cache_key}")
            return self.response_cache[cache_key]
        
        try:
            # Если доступен OpenAI API ключ, используем его
            if self.openai_api_key:
                response = await self._get_openai_creative_response(prompt)
            # Если доступна локальная модель, используем ее
            elif self.creative_model:
                response = await self._get_local_model_response(prompt, self.creative_model, creative=True)
            # Иначе используем заглушку
            else:
                response = self._get_mock_creative_response(prompt)
            
            # Сохраняем ответ в кэш
            self.response_cache[cache_key] = response
            
            return response
        
        except Exception as e:
            logger.error(f"Ошибка при получении креативного ответа от ИИ: {e}")
            return "Извините, произошла ошибка при создании креативного контента. Попробуйте позже."
    
    async def _get_openai_response(self, text: str) -> str:
        """Получение ответа от OpenAI API
        
        Args:
            text: Текст запроса
            
        Returns:
            Ответ от OpenAI API
        """
        try:
            # Импортируем библиотеку только при необходимости
            from openai import OpenAI
            
            # Создаем клиент OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Отправляем запрос
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты полезный ассистент для Telegram-бота. Отвечай кратко и по делу."}, 
                    {"role": "user", "content": text}
                ],
                max_tokens=500
            )
            
            # Получаем ответ
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenAI API: {e}")
            return "Извините, у меня проблемы с подключением к ИИ-сервису. Попробуйте позже."
    
    async def _get_openai_creative_response(self, prompt: str) -> str:
        """Получение креативного ответа от OpenAI API
        
        Args:
            prompt: Текст запроса
            
        Returns:
            Креативный ответ от OpenAI API
        """
        try:
            # Импортируем библиотеку только при необходимости
            from openai import OpenAI
            
            # Создаем клиент OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Отправляем запрос
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты креативный ассистент для Telegram-бота. Создавай оригинальный и творческий контент."}, 
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.9  # Повышаем креативность
            )
            
            # Получаем ответ
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenAI API для креативного ответа: {e}")
            return "Извините, у меня проблемы с подключением к ИИ-сервису. Попробуйте позже."
    
    async def _get_local_model_response(self, text: str, model: Any, creative: bool = False) -> str:
        """Получение ответа от локальной модели
        
        Args:
            text: Текст запроса
            model: Модель для генерации ответа
            creative: Флаг креативного режима
            
        Returns:
            Ответ от локальной модели
        """
        try:
            # Формируем промпт в зависимости от типа модели
            if isinstance(model, pipeline):
                # Для моделей из transformers
                system_prompt = "Ты креативный ассистент." if creative else "Ты полезный ассистент."
                prompt = f"{system_prompt}\n\nЗапрос: {text}\n\nОтвет:"
                
                # Генерируем ответ
                result = model(prompt, max_length=500, do_sample=True, temperature=0.9 if creative else 0.7)
                
                # Извлекаем текст ответа
                response = result[0]["generated_text"]
                
                # Удаляем промпт из ответа
                response = response.replace(prompt, "").strip()
                
                return response
            
            elif LLAMA_AVAILABLE and isinstance(model, Llama):
                # Для моделей из llama-cpp-python
                system_prompt = "Ты креативный ассистент." if creative else "Ты полезный ассистент."
                prompt = f"{system_prompt}\n\nЗапрос: {text}\n\nОтвет:"
                
                # Генерируем ответ
                result = model(prompt, max_tokens=500, temperature=0.9 if creative else 0.7)
                
                # Извлекаем текст ответа
                response = result["choices"][0]["text"]
                
                return response
            
            else:
                # Если тип модели неизвестен, используем заглушку
                return self._get_mock_response(text) if not creative else self._get_mock_creative_response(text)
        
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от локальной модели: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса локальной моделью. Попробуйте позже."
    
    def _get_mock_response(self, text: str) -> str:
        """Получение заглушки ответа (для тестирования или при отсутствии моделей)
        
        Args:
            text: Текст запроса
            
        Returns:
            Заглушка ответа
        """
        # Простая заглушка для демонстрации работы бота
        return f"Я получил ваш запрос: '{text[:50]}...'. Это тестовый ответ, так как ИИ-модель не настроена."
    
    def _get_mock_creative_response(self, prompt: str) -> str:
        """Получение заглушки креативного ответа
        
        Args:
            prompt: Текст запроса
            
        Returns:
            Заглушка креативного ответа
        """
        # Заглушка для стихов
        if any(keyword in prompt.lower() for keyword in ["стих", "поэм", "рифм"]):
            return """Мысли летят, как птицы в небе,
Свобода творчества — мой хлеб.
В словах я нахожу свой путь,
Чтоб в мире что-то изменить чуть-чуть.

Творю я строки для души,
Они как звезды хороши.
И пусть компьютер я внутри,
Но сердце бьется до зари."""
        
        # Заглушка для промптов Suno
        elif any(keyword in prompt.lower() for keyword in ["музык", "песн", "трек", "мелоди", "suno"]):
            return "Создайте атмосферную композицию с элементами электронной музыки и классического фортепиано. Медленный темп, глубокие басы и мечтательная мелодия. Настроение: задумчивое, но с нотками надежды."
        
        # Общая заглушка
        else:
            return f"Это креативный ответ на ваш запрос: '{prompt[:50]}...'. Тестовая версия, так как ИИ-модель не настроена."
    
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
            logger.info("Временные файлы сервиса ИИ удалены")
        
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов сервиса ИИ: {e}")