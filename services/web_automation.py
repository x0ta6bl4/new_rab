#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для автоматизации веб-интерфейсов
Предоставляет функциональность для взаимодействия с веб-сайтами через браузер
"""

import os
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger

# Импортируем Playwright для автоматизации браузера
try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Библиотека playwright не установлена. Установите её командой: pip install playwright")
    logger.warning("После установки выполните: playwright install chromium")


class WebAutomation:
    """Класс для автоматизации веб-интерфейсов"""
    
    def __init__(self):
        """Инициализация сервиса веб-автоматизации"""
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot_web_automation"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Флаг доступности Playwright
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        
        # Объекты Playwright
        self.playwright = None
        self.browser = None
        
        logger.info("Сервис веб-автоматизации инициализирован")
    
    async def start_browser(self, headless: bool = True) -> bool:
        """Запуск браузера
        
        Args:
            headless: Запускать ли браузер в фоновом режиме
            
        Returns:
            True, если браузер успешно запущен, иначе False
        """
        if not self.playwright_available:
            logger.error("Playwright не установлен. Невозможно запустить браузер.")
            return False
        
        try:
            # Запускаем Playwright
            self.playwright = await async_playwright().start()
            
            # Запускаем браузер
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=["--disable-dev-shm-usage", "--no-sandbox"]
            )
            
            logger.info(f"Браузер успешно запущен (headless={headless})")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера: {e}")
            return False
    
    async def close_browser(self):
        """Закрытие браузера"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            logger.info("Браузер успешно закрыт")
        
        except Exception as e:
            logger.error(f"Ошибка при закрытии браузера: {e}")
    
    async def create_suno_track(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Создание музыкального трека через веб-интерфейс Suno
        
        Args:
            prompt: Промпт для создания трека
            max_retries: Максимальное количество попыток
            
        Returns:
            URL созданного трека или None в случае ошибки
        """
        if not self.playwright_available:
            logger.error("Playwright не установлен. Невозможно создать трек через веб-интерфейс.")
            return None
        
        # Запускаем браузер, если он еще не запущен
        if not self.browser:
            success = await self.start_browser(headless=True)
            if not success:
                return None
        
        try:
            # Создаем новую страницу
            page = await self.browser.new_page()
            
            # Устанавливаем таймаут
            page.set_default_timeout(60000)  # 60 секунд
            
            # Открываем Suno
            await page.goto("https://suno.ai/")
            logger.info("Открыта страница Suno")
            
            # Проверяем, нужно ли авторизоваться
            if await self._check_login_required(page):
                success = await self._login_to_suno(page)
                if not success:
                    logger.error("Не удалось авторизоваться в Suno")
                    await page.close()
                    return None
            
            # Переходим на страницу создания трека
            await page.goto("https://suno.ai/create")
            logger.info("Открыта страница создания трека")
            
            # Вводим промпт
            await page.fill("textarea[placeholder='Describe your song']", prompt)
            logger.info(f"Введен промпт: {prompt[:50]}...")
            
            # Нажимаем кнопку создания трека
            await page.click("button:has-text('Create')")
            logger.info("Нажата кнопка создания трека")
            
            # Ждем создания трека (может занять некоторое время)
            track_url = await self._wait_for_track_creation(page)
            
            # Закрываем страницу
            await page.close()
            
            return track_url
        
        except Exception as e:
            logger.error(f"Ошибка при создании трека через веб-интерфейс Suno: {e}")
            
            # Пробуем еще раз, если есть попытки
            if max_retries > 0:
                logger.info(f"Повторная попытка создания трека ({max_retries} осталось)")
                return await self.create_suno_track(prompt, max_retries - 1)
            
            return None
    
    async def _check_login_required(self, page: Page) -> bool:
        """Проверка необходимости авторизации
        
        Args:
            page: Объект страницы Playwright
            
        Returns:
            True, если требуется авторизация, иначе False
        """
        try:
            # Проверяем наличие кнопки логина
            login_button = await page.query_selector("text=Log in")
            return login_button is not None
        
        except Exception as e:
            logger.error(f"Ошибка при проверке необходимости авторизации: {e}")
            return True  # Предполагаем, что авторизация нужна
    
    async def _login_to_suno(self, page: Page) -> bool:
        """Авторизация в Suno через Google
        
        Args:
            page: Объект страницы Playwright
            
        Returns:
            True, если авторизация успешна, иначе False
        """
        try:
            # Нажимаем кнопку логина
            await page.click("text=Log in")
            logger.info("Нажата кнопка логина")
            
            # Ждем появления формы логина и нажимаем на кнопку входа через Google
            await page.wait_for_selector("button:has-text('Continue with Google')")
            await page.click("button:has-text('Continue with Google')")
            logger.info("Выбран вход через Google")
            
            # Ждем перехода на страницу авторизации Google
            await page.wait_for_url("*accounts.google.com*", timeout=10000)
            
            # Вводим email Google
            google_email = os.getenv("GOOGLE_AUTH_EMAIL")
            if not google_email:
                logger.error("Не найден email для авторизации Google в переменных окружения")
                return False
                
            await page.fill("input[type=email]", google_email)
            await page.click("button:has-text('Next')")
            
            # Ждем появления поля для ввода пароля
            await page.wait_for_selector("input[type=password]", timeout=10000)
            
            # Вводим пароль Google
            google_password = os.getenv("GOOGLE_AUTH_PASSWORD")
            if not google_password:
                logger.error("Не найден пароль для авторизации Google в переменных окружения")
                return False
                
            await page.fill("input[type=password]", google_password)
            await page.click("button:has-text('Next')")
            
            # Ждем успешной авторизации и перенаправления обратно на Suno
            try:
                await page.wait_for_selector("text=Create", timeout=20000)
                logger.info("Успешная авторизация в Suno через Google")
                return True
            except PlaywrightTimeoutError:
                logger.error("Таймаут при ожидании успешной авторизации через Google")
                return False
        
        except Exception as e:
            logger.error(f"Ошибка при авторизации в Suno через Google: {e}")
            return False
    
    async def _wait_for_track_creation(self, page: Page) -> Optional[str]:
        """Ожидание создания трека
        
        Args:
            page: Объект страницы Playwright
            
        Returns:
            URL созданного трека или None в случае ошибки
        """
        try:
            # Ждем появления индикатора прогресса
            await page.wait_for_selector("text=Creating your track", timeout=10000)
            logger.info("Началось создание трека")
            
            # Ждем исчезновения индикатора прогресса (макс. 5 минут)
            await page.wait_for_selector("text=Creating your track", state="hidden", timeout=300000)
            logger.info("Трек создан")
            
            # Получаем URL трека
            # Обычно после создания трека происходит редирект на страницу с треком
            current_url = page.url
            
            if "track" in current_url:
                logger.info(f"Получен URL трека: {current_url}")
                return current_url
            
            # Если редиректа не произошло, ищем ссылку на трек
            track_link = await page.query_selector("a[href*='track']")
            if track_link:
                href = await track_link.get_attribute("href")
                full_url = f"https://suno.ai{href}" if href.startswith("/") else href
                logger.info(f"Получен URL трека: {full_url}")
                return full_url
            
            logger.error("Не удалось получить URL трека")
            return None
        
        except PlaywrightTimeoutError:
            logger.error("Таймаут при ожидании создания трека")
            return None
        
        except Exception as e:
            logger.error(f"Ошибка при ожидании создания трека: {e}")
            return None
    
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
            logger.info("Временные файлы веб-автоматизации удалены")
        
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов веб-автоматизации: {e}")