# PowerShell скрипт для генерации SSH-ключей для автоматического деплоя

# Настройки
$KEY_NAME = "deploy_key"
$KEY_COMMENT = "key for automatic deployment"
$SSH_DIR = "$env:USERPROFILE\.ssh"

# Создание директории .ssh, если она не существует
if (-not (Test-Path $SSH_DIR)) {
    New-Item -ItemType Directory -Path $SSH_DIR | Out-Null
    Write-Host "Создана директория $SSH_DIR" -ForegroundColor Green
}

# Проверка наличия ssh-keygen
if (-not (Get-Command ssh-keygen -ErrorAction SilentlyContinue)) {
    Write-Host "Ошибка: Утилита ssh-keygen не найдена. Установите OpenSSH для продолжения." -ForegroundColor Red
    Write-Host "Вы можете установить OpenSSH через 'Параметры Windows > Приложения > Дополнительные компоненты > Добавить компонент > OpenSSH Client'" -ForegroundColor Yellow
    exit 1
}

# Проверка существования ключей
$PRIVATE_KEY_PATH = "$SSH_DIR\$KEY_NAME"
$PUBLIC_KEY_PATH = "$SSH_DIR\$KEY_NAME.pub"

if (Test-Path $PRIVATE_KEY_PATH) {
    Write-Host "Внимание: Файл $PRIVATE_KEY_PATH уже существует." -ForegroundColor Yellow
    $overwrite = Read-Host "Хотите перезаписать существующий ключ? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "Операция отменена." -ForegroundColor Yellow
        exit 0
    }
}

# Генерация SSH-ключей
Write-Host "Генерация новой пары SSH-ключей..." -ForegroundColor Cyan
ssh-keygen -t rsa -b 4096 -C $KEY_COMMENT -f $PRIVATE_KEY_PATH -N ""

if ($LASTEXITCODE -eq 0) {
    Write-Host "\nSSH-ключи успешно созданы:" -ForegroundColor Green
    Write-Host "Приватный ключ: $PRIVATE_KEY_PATH" -ForegroundColor Green
    Write-Host "Публичный ключ: $PUBLIC_KEY_PATH" -ForegroundColor Green
    
    # Вывод инструкций
    Write-Host "\nДальнейшие шаги:" -ForegroundColor Cyan
    Write-Host "1. Добавьте публичный ключ на ваш сервер в файл ~/.ssh/authorized_keys" -ForegroundColor White
    Write-Host "2. Добавьте приватный ключ в секреты GitHub или GitLab" -ForegroundColor White
    Write-Host "3. Обновите настройки деплоя в файлах конфигурации" -ForegroundColor White
    
    # Вывод содержимого публичного ключа
    Write-Host "\nСодержимое публичного ключа:" -ForegroundColor Cyan
    Get-Content $PUBLIC_KEY_PATH
} else {
    Write-Host "Ошибка при генерации SSH-ключей." -ForegroundColor Red
}