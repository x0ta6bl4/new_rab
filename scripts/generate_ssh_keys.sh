#!/bin/bash

# Скрипт для генерации SSH-ключей для автоматического деплоя

# Настройки
KEY_NAME="deploy_key"
KEY_COMMENT="key for automatic deployment"
SSH_DIR="$HOME/.ssh"

# Цвета для вывода
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m" # No Color

# Создание директории .ssh, если она не существует
if [ ! -d "$SSH_DIR" ]; then
    mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    echo -e "${GREEN}Создана директория $SSH_DIR${NC}"
fi

# Проверка наличия ssh-keygen
if ! command -v ssh-keygen &> /dev/null; then
    echo -e "${RED}Ошибка: Утилита ssh-keygen не найдена. Установите OpenSSH для продолжения.${NC}"
    exit 1
fi

# Проверка существования ключей
PRIVATE_KEY_PATH="$SSH_DIR/$KEY_NAME"
PUBLIC_KEY_PATH="$SSH_DIR/$KEY_NAME.pub"

if [ -f "$PRIVATE_KEY_PATH" ]; then
    echo -e "${YELLOW}Внимание: Файл $PRIVATE_KEY_PATH уже существует.${NC}"
    read -p "Хотите перезаписать существующий ключ? (y/n): " overwrite
    if [ "$overwrite" != "y" ]; then
        echo -e "${YELLOW}Операция отменена.${NC}"
        exit 0
    fi
fi

# Генерация SSH-ключей
echo -e "${CYAN}Генерация новой пары SSH-ключей...${NC}"
ssh-keygen -t rsa -b 4096 -C "$KEY_COMMENT" -f "$PRIVATE_KEY_PATH" -N ""

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}SSH-ключи успешно созданы:${NC}"
    echo -e "${GREEN}Приватный ключ: $PRIVATE_KEY_PATH${NC}"
    echo -e "${GREEN}Публичный ключ: $PUBLIC_KEY_PATH${NC}"
    
    # Установка правильных прав доступа
    chmod 600 "$PRIVATE_KEY_PATH"
    chmod 644 "$PUBLIC_KEY_PATH"
    
    # Вывод инструкций
    echo -e "\n${CYAN}Дальнейшие шаги:${NC}"
    echo -e "1. Добавьте публичный ключ на ваш сервер в файл ~/.ssh/authorized_keys"
    echo -e "2. Добавьте приватный ключ в секреты GitHub или GitLab"
    echo -e "3. Обновите настройки деплоя в файлах конфигурации"
    
    # Вывод содержимого публичного ключа
    echo -e "\n${CYAN}Содержимое публичного ключа:${NC}"
    cat "$PUBLIC_KEY_PATH"
    
    # Инструкция по добавлению ключа на сервер
    echo -e "\n${CYAN}Для добавления ключа на сервер выполните:${NC}"
    echo -e "ssh-copy-id -i $PUBLIC_KEY_PATH user@server_host"
else
    echo -e "${RED}Ошибка при генерации SSH-ключей.${NC}"
fi