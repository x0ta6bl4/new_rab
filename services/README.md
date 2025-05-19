# Модуль веб-автоматизации

Этот модуль предоставляет функциональность для автоматизации взаимодействия с веб-интерфейсами через браузер, используя библиотеку Playwright.

## Установка зависимостей

Для работы модуля необходимо установить следующие зависимости:

```bash
pip install playwright
playwright install chromium
```

## Использование

### Автоматизация Suno

Модуль `web_automation.py` предоставляет класс `WebAutomation` для взаимодействия с веб-интерфейсом Suno. Основная функциональность:

- Автоматический вход в аккаунт Suno
- Создание музыкальных треков через веб-интерфейс
- Получение URL созданного трека

### Настройка учетных данных

Для работы с веб-интерфейсом Suno через авторизацию Google необходимо указать учетные данные в файле `keys.env`:

```
GOOGLE_AUTH_EMAIL=your_email@gmail.com
GOOGLE_AUTH_PASSWORD=your_google_password
```

### Пример использования

```python
from services.web_automation import WebAutomation

async def create_track():
    web_automation = WebAutomation()
    try:
        # Запуск браузера
        await web_automation.start_browser(headless=True)
        
        # Создание трека
        prompt = "Create an upbeat pop song with electronic elements"
        track_url = await web_automation.create_suno_track(prompt)
        
        if track_url:
            print(f"Трек создан: {track_url}")
        else:
            print("Не удалось создать трек")
    finally:
        # Закрытие браузера
        await web_automation.close_browser()
        web_automation.cleanup()
```

## Интеграция с ботом поэзии

Модуль интегрирован с классом `SunoIntegration` в боте поэзии. Интеграция автоматически использует веб-интерфейс для создания треков, а в случае ошибки пытается использовать API метод (если доступен API ключ).

## Примечания

- Для работы в фоновом режиме используется параметр `headless=True` при запуске браузера
- В случае проблем с авторизацией, проверьте правильность учетных данных в `keys.env`
- Создание трека может занимать до 5 минут, в зависимости от загруженности серверов Suno