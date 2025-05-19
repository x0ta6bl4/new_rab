# PowerShell скрипт для деплоя Telegram-бота на сервер

# Настройки сервера
$SERVER_USER = "user"
$SERVER_HOST = "your-server-host"
$SERVER_PATH = "/path/to/telegram-bot"

# Функция для вывода сообщений с цветом
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Yellow "Начинаем деплой Telegram-бота на сервер..."

# Проверка наличия необходимых утилит
if (-not (Get-Command ssh -ErrorAction SilentlyContinue) -or -not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Ошибка: Утилиты ssh и/или scp не найдены. Установите OpenSSH для продолжения."
    exit 1
}

# Создание архива проекта
Write-ColorOutput Yellow "Создание архива проекта..."
Compress-Archive -Path .\* -DestinationPath .\telegram_bot.zip -Force -Exclude ".git", "__pycache__", "*.pyc", ".env"

# Копирование архива на сервер
Write-ColorOutput Yellow "Копирование файлов на сервер..."
scp .\telegram_bot.zip "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}"

# Удаление локального архива
Remove-Item .\telegram_bot.zip -Force

# Подключение к серверу и распаковка архива
Write-ColorOutput Yellow "Распаковка архива на сервере и запуск контейнеров..."
$sshCommand = @"
cd "$SERVER_PATH"
unzip -o telegram_bot.zip
rm telegram_bot.zip

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
"@

ssh "${SERVER_USER}@${SERVER_HOST}" "$sshCommand"

# Проверка результата
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput Green "Деплой успешно завершен!"
}
else {
    Write-ColorOutput Red "Ошибка при выполнении деплоя."
    exit 1
}