#!/bin/bash

# Скрипт для настройки webhook на сервере
# Этот скрипт устанавливает и настраивает webhook для автоматического деплоя

# Цвета для вывода
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Проверка наличия необходимых утилит
command -v jq >/dev/null 2>&1 || { echo -e "${RED}Ошибка: jq не установлен. Установите его с помощью 'apt-get install jq'.${NC}"; exit 1; }

# Параметры для настройки
WEBHOOK_PORT=9000
SECRET_TOKEN="your-secret-token" # Измените на свой секретный токен
REPO_PATH="/path/to/your/repo" # Путь к репозиторию на сервере

# Установка webhook, если он не установлен
if ! command -v webhook >/dev/null 2>&1; then
    echo -e "${YELLOW}Установка webhook...${NC}"
    apt-get update
    apt-get install -y webhook
    if [ $? -ne 0 ]; then
        echo -e "${RED}Не удалось установить webhook. Установите его вручную.${NC}"
        exit 1
    fi
fi

# Создание директории для конфигурации webhook
mkdir -p /etc/webhook

# Создание конфигурационного файла для webhook
cat > /etc/webhook/hooks.json << EOF
[
  {
    "id": "deploy-telegram-bot",
    "execute-command": "${REPO_PATH}/scripts/webhook_deploy.sh",
    "command-working-directory": "${REPO_PATH}",
    "response-message": "Запущен процесс деплоя",
    "trigger-rule": {
      "match": {
        "type": "payload-hash-sha1",
        "secret": "${SECRET_TOKEN}",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature"
        }
      }
    }
  }
]
EOF

# Создание скрипта для выполнения деплоя при получении webhook
cat > ${REPO_PATH}/scripts/webhook_deploy.sh << EOF
#!/bin/bash

# Логирование
LOG_FILE="${REPO_PATH}/webhook_deploy.log"
echo "[\$(date)] Получен webhook, начинаем деплой" >> \$LOG_FILE

# Переход в директорию репозитория
cd ${REPO_PATH}

# Обновление кода из репозитория
git pull

# Запуск контейнеров
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "[\$(date)] Деплой завершен" >> \$LOG_FILE
EOF

# Установка прав на скрипт
chmod +x ${REPO_PATH}/scripts/webhook_deploy.sh

# Создание systemd сервиса для webhook
cat > /etc/systemd/system/webhook.service << EOF
[Unit]
Description=Webhook для автоматического деплоя
After=network.target

[Service]
ExecStart=/usr/bin/webhook -hooks /etc/webhook/hooks.json -port ${WEBHOOK_PORT} -verbose
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd, включение и запуск сервиса
systemctl daemon-reload
systemctl enable webhook.service
systemctl start webhook.service

# Проверка статуса сервиса
if systemctl is-active --quiet webhook.service; then
    echo -e "${GREEN}Webhook успешно настроен и запущен на порту ${WEBHOOK_PORT}${NC}"
    echo -e "${YELLOW}Инструкции по настройке webhook в GitHub/GitLab:${NC}"
    echo -e "1. Перейдите в настройки репозитория -> Webhooks -> Add webhook"
    echo -e "2. Укажите URL: http://your-server-ip:${WEBHOOK_PORT}/hooks/deploy-telegram-bot"
    echo -e "3. Укажите Content type: application/json"
    echo -e "4. Укажите Secret: ${SECRET_TOKEN}"
    echo -e "5. Выберите события: Push events"
    echo -e "6. Сохраните webhook"
else
    echo -e "${RED}Не удалось запустить webhook сервис. Проверьте логи: journalctl -u webhook.service${NC}"
    exit 1
fi