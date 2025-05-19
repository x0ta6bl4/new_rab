#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик голосовых сообщений для главного бота
Отвечает за преобразование голосовых сообщений в текст
"""

import os
import tempfile
from pathlib import Path
import speech_recognition as sr
from pydub import AudioSegment
from loguru import logger


class VoiceHandler:
    """Класс для обработки голосовых сообщений"""
    
    def __init__(self):
        """Инициализация обработчика голосовых сообщений"""
        self.recognizer = sr.Recognizer()
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_voice_processing"
        self.temp_dir.mkdir(exist_ok=True)
        logger.info("Обработчик голосовых сообщений инициализирован")
    
    async def speech_to_text(self, voice_path: Path) -> str:
        """Преобразование голосового сообщения в текст
        
        Args:
            voice_path: Путь к файлу с голосовым сообщением
            
        Returns:
            Распознанный текст или пустая строка в случае ошибки
        """
        try:
            # Конвертируем OGG в WAV для распознавания
            wav_path = self.temp_dir / f"{voice_path.stem}.wav"
            
            # Используем pydub для конвертации
            audio = AudioSegment.from_file(voice_path, format="ogg")
            audio.export(wav_path, format="wav")
            
            # Распознаем речь
            with sr.AudioFile(str(wav_path)) as source:
                audio_data = self.recognizer.record(source)
                
                # Пытаемся распознать с помощью Google Speech Recognition (бесплатно с ограничениями)
                text = self.recognizer.recognize_google(audio_data, language="ru-RU")
                logger.info(f"Распознан текст: {text[:50]}...")
                return text
        
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition не смог распознать аудио")
            return ""
        
        except sr.RequestError as e:
            logger.error(f"Не удалось запросить результаты у Google Speech Recognition; {e}")
            return ""
        
        except Exception as e:
            logger.error(f"Ошибка при распознавании речи: {e}")
            return ""
        
        finally:
            # Удаляем временный WAV-файл
            if 'wav_path' in locals() and wav_path.exists():
                try:
                    wav_path.unlink()
                except Exception as e:
                    logger.error(f"Ошибка при удалении временного файла {wav_path}: {e}")
    
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
            logger.info("Временные файлы обработчика голосовых сообщений удалены")
        
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов обработчика голосовых сообщений: {e}")