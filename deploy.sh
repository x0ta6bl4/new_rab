#!/bin/bash

# Скрипт для деплоя Telegram-бота на сервер

# Настройки сервера
SERVER_USER="user"
SERVER_HOST="your-server-host"
SERVER_PATH="/path/to/telegram-bot"

# Цвета для вывода
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${YELLOW}Начинаем деплой Telegram-бота на сервер...${NC}"

# Проверка наличия необходимых утилит
if ! command -v ssh &> /dev/null || ! command -v scp &> /dev/null; then
    echo -e "${RED}Ошибка: Утилиты ssh и/или scp не найдены. Установите их для продолжения.${NC}"
    exit 1
fi

# Создание архива проекта
echo -e "${YELLOW}Создание архива проекта...${NC}"
tar --exclude=".git" --exclude="__pycache__" --exclude="*.pyc" --exclude=".env" -czf telegram_bot.tar.gz .

# Копирование архива на сервер
echo -e "${YELLOW}Копирование файлов на сервер...${NC}"
scp telegram_bot.tar.gz "$SERVER_USER@$SERVER_HOST:$SERVER_PATH"

# Удаление локального архива
rm telegram_bot.tar.gz

# Подключение к серверу и распаковка архива
echo -e "${YELLOW}Распаковка архива на сервере и запуск контейнеров...${NC}"
ssh "$SERVER_USER@$SERVER_HOST" << EOF
    cd "$SERVER_PATH"
    tar -xzf telegram_bot.tar.gz
    rm telegram_bot.tar.gz
    
    # Проверка наличия Docker и Docker Compose
    if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
        echo "Ошибка: Docker и/или Docker Compose не установлены на сервере."
        exit 1
    fi
    
    # Запуск контейнеров
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    # Проверка статуса контейнеров
    docker-compose ps
EOF

# Проверка результата
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Деплой успешно завершен!${NC}"
else
    echo -e "${RED}Ошибка при выполнении деплоя.${NC}"
    exit 1
fi