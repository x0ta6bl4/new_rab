#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для работы с базой данных
Отвечает за инициализацию базы данных и предоставление интерфейса для работы с ней
"""

import os
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent / "database" / "bot.db"


def init_db():
    """Инициализация базы данных"""
    # Создаем директорию для базы данных, если она не существует
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создаем таблицы
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,         -- Telegram user ID
        username TEXT,                       -- Username (@username)
        first_name TEXT,                     -- User's first name
        last_name TEXT,                      -- User's last name
        language_code TEXT,                  -- User's language code
        is_premium BOOLEAN DEFAULT 0,        -- Premium status flag
        registration_date TEXT,              -- Registration date
        last_activity TEXT,                  -- Last activity
        settings TEXT                        -- User settings in JSON
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique message ID
        user_id INTEGER,                      -- User ID
        message_text TEXT,                    -- Message text
        message_type TEXT,                    -- Message type (text, photo, voice, etc.)
        timestamp TEXT,                       -- Sending time
        is_bot_message BOOLEAN DEFAULT 0,     -- Bot message flag
        bot_name TEXT,                        -- Name of the bot that processed the message
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique stat ID
        bot_name TEXT,                        -- Name of the bot
        request_count INTEGER DEFAULT 0,      -- Number of requests
        success_count INTEGER DEFAULT 0,      -- Number of successful responses
        error_count INTEGER DEFAULT 0,        -- Number of errors
        last_request TEXT                     -- Last request time
    )
    """)
    
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
    
    logger.info(f"База данных инициализирована: {DB_PATH}")


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        """Инициализация объекта базы данных"""
        self.db_path = DB_PATH
        logger.info(f"Объект базы данных инициализирован: {self.db_path}")
    
    def _get_connection(self):
        """Получение соединения с базой данных
        
        Returns:
            Соединение с базой данных
        """
        return sqlite3.connect(self.db_path)
    
    def save_user(self, user_id: int, username: str = None, first_name: str = None, 
                  last_name: str = None, language_code: str = None, is_premium: bool = False):
        """Сохранение информации о пользователе
        
        Args:
            user_id: ID пользователя
            username: Имя пользователя
            first_name: Имя
            last_name: Фамилия
            language_code: Код языка
            is_premium: Флаг премиум-статуса
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Проверяем, существует ли пользователь
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            user_exists = cursor.fetchone()
            
            if user_exists:
                # Обновляем информацию о пользователе
                cursor.execute("""
                UPDATE users SET 
                    username = COALESCE(?, username),
                    first_name = COALESCE(?, first_name),
                    last_name = COALESCE(?, last_name),
                    language_code = COALESCE(?, language_code),
                    is_premium = COALESCE(?, is_premium),
                    last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """, (username, first_name, last_name, language_code, is_premium, user_id))
            else:
                # Добавляем нового пользователя
                cursor.execute("""
                INSERT INTO users (
                    user_id, username, first_name, last_name, 
                    language_code, is_premium, registration_date, last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, username, first_name, last_name, language_code, is_premium))
            
            conn.commit()
            logger.debug(f"Информация о пользователе {user_id} сохранена")
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении информации о пользователе {user_id}: {e}")
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def save_message(self, user_id: int, message_text: str, message_type: str, 
                     is_bot_message: bool = False, bot_name: str = None):
        """Сохранение сообщения
        
        Args:
            user_id: ID пользователя
            message_text: Текст сообщения
            message_type: Тип сообщения
            is_bot_message: Флаг сообщения от бота
            bot_name: Имя бота, обработавшего сообщение
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Добавляем сообщение
            cursor.execute("""
            INSERT INTO messages (
                user_id, message_text, message_type, timestamp, is_bot_message, bot_name
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            """, (user_id, message_text, message_type, is_bot_message, bot_name))
            
            # Обновляем время последней активности пользователя
            cursor.execute("""
            UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            logger.debug(f"Сообщение от пользователя {user_id} сохранено")
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения от пользователя {user_id}: {e}")
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def update_bot_stats(self, bot_name: str, success: bool = True):
        """Обновление статистики бота
        
        Args:
            bot_name: Имя бота
            success: Флаг успешного ответа
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Проверяем, существует ли запись для бота
            cursor.execute("SELECT bot_name FROM bot_stats WHERE bot_name = ?", (bot_name,))
            bot_exists = cursor.fetchone()
            
            if bot_exists:
                # Обновляем статистику
                if success:
                    cursor.execute("""
                    UPDATE bot_stats SET 
                        request_count = request_count + 1,
                        success_count = success_count + 1,
                        last_request = CURRENT_TIMESTAMP
                    WHERE bot_name = ?
                    """, (bot_name,))
                else:
                    cursor.execute("""
                    UPDATE bot_stats SET 
                        request_count = request_count + 1,
                        error_count = error_count + 1,
                        last_request = CURRENT_TIMESTAMP
                    WHERE bot_name = ?
                    """, (bot_name,))
            else:
                # Добавляем новую запись
                if success:
                    cursor.execute("""
                    INSERT INTO bot_stats (
                        bot_name, request_count, success_count, error_count, last_request
                    ) VALUES (?, 1, 1, 0, CURRENT_TIMESTAMP)
                    """, (bot_name,))
                else:
                    cursor.execute("""
                    INSERT INTO bot_stats (
                        bot_name, request_count, success_count, error_count, last_request
                    ) VALUES (?, 1, 0, 1, CURRENT_TIMESTAMP)
                    """, (bot_name,))
            
            conn.commit()
            logger.debug(f"Статистика бота {bot_name} обновлена")
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики бота {bot_name}: {e}")
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Информация о пользователе или None, если пользователь не найден
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row  # Для получения результатов в виде словаря
            cursor = conn.cursor()
            
            # Получаем информацию о пользователе
            cursor.execute("""
            SELECT * FROM users WHERE user_id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            else:
                return None
        
        except Exception as e:
            logger.error(f"Ошибка при получении информации о пользователе {user_id}: {e}")
            return None
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_user_messages(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних сообщений пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество сообщений
            
        Returns:
            Список сообщений
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row  # Для получения результатов в виде словаря
            cursor = conn.cursor()
            
            # Получаем последние сообщения пользователя
            cursor.execute("""
            SELECT * FROM messages 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (user_id, limit))
            
            messages = cursor.fetchall()
            
            return [dict(message) for message in messages]
        
        except Exception as e:
            logger.error(f"Ошибка при получении сообщений пользователя {user_id}: {e}")
            return []
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_bot_stats(self, bot_name: str = None) -> List[Dict[str, Any]]:
        """Получение статистики ботов
        
        Args:
            bot_name: Имя бота (если None, то для всех ботов)
            
        Returns:
            Статистика ботов
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row  # Для получения результатов в виде словаря
            cursor = conn.cursor()
            
            if bot_name:
                # Получаем статистику для конкретного бота
                cursor.execute("""
                SELECT * FROM bot_stats WHERE bot_name = ?
                """, (bot_name,))
            else:
                # Получаем статистику для всех ботов
                cursor.execute("""
                SELECT * FROM bot_stats
                """)
            
            stats = cursor.fetchall()
            
            return [dict(stat) for stat in stats]
        
        except Exception as e:
            logger.error(f"Ошибка при получении статистики ботов: {e}")
            return []
        e
        finally:
            if 'conn' in locals():
                conn.close()