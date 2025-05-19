# Скрипт для настройки webhook на Windows-сервере
# Этот скрипт устанавливает и настраивает webhook для автоматического деплоя

# Функция для цветного вывода
function Write-ColorOutput {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Color,
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    
    $originalColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $Color
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $originalColor
}

# Параметры для настройки
$WEBHOOK_PORT = 9000
$SECRET_TOKEN = "your-secret-token" # Измените на свой секретный токен
$REPO_PATH = "C:\path\to\your\repo" # Путь к репозиторию на сервере

# Проверка наличия Chocolatey
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Yellow "Установка Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Red "Не удалось установить Chocolatey. Установите его вручную."
        exit 1
    }
}

# Установка webhook-relay, так как webhook не имеет официального пакета для Windows
Write-ColorOutput Yellow "Установка webhook-relay..."
choco install -y ngrok
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Не удалось установить ngrok. Установите его вручную."
    exit 1
}

# Создание директории для скриптов, если она не существует
if (!(Test-Path "$REPO_PATH\scripts")) {
    New-Item -ItemType Directory -Path "$REPO_PATH\scripts" -Force
}

# Создание скрипта для выполнения деплоя при получении webhook
$webhookDeployScript = @"
# Скрипт для выполнения деплоя при получении webhook

# Логирование
\$LOG_FILE = "$REPO_PATH\webhook_deploy.log"
Add-Content -Path \$LOG_FILE -Value "[`$(Get-Date)] Получен webhook, начинаем деплой"

# Переход в директорию репозитория
Set-Location -Path "$REPO_PATH"

# Обновление кода из репозитория
git pull

# Запуск контейнеров
docker-compose down
docker-compose build --no-cache
docker-compose up -d

Add-Content -Path \$LOG_FILE -Value "[`$(Get-Date)] Деплой завершен"
"@

Set-Content -Path "$REPO_PATH\scripts\webhook_deploy.ps1" -Value $webhookDeployScript

# Создание конфигурационного файла для ngrok
$ngrokConfig = @"
{{
  "authtoken": "YOUR_NGROK_AUTH_TOKEN",
  "tunnels": {{
    "webhook": {{
      "proto": "http",
      "addr": "$WEBHOOK_PORT"
    }}
  }}
}}
"@

Set-Content -Path "$env:USERPROFILE\AppData\Local\ngrok\ngrok.yml" -Value $ngrokConfig

# Создание простого HTTP сервера на PowerShell для обработки webhook
$webhookServerScript = @"
# Простой HTTP сервер для обработки webhook

\$port = $WEBHOOK_PORT
\$secretToken = "$SECRET_TOKEN"
\$deployScriptPath = "$REPO_PATH\scripts\webhook_deploy.ps1"

# Создание HTTP-слушателя
\$listener = New-Object System.Net.HttpListener
\$listener.Prefixes.Add("http://+:\$port/")

try {{
    \$listener.Start()
    Write-Host "Webhook сервер запущен на порту \$port"
    
    while (\$listener.IsListening) {{
        \$context = \$listener.GetContext()
        \$request = \$context.Request
        \$response = \$context.Response
        
        # Проверка пути
        if (\$request.Url.LocalPath -eq "/hooks/deploy-telegram-bot") {{
            # Проверка метода
            if (\$request.HttpMethod -eq "POST") {{
                # Проверка заголовка X-Hub-Signature
                \$signature = \$request.Headers["X-Hub-Signature"]
                \$isValid = \$false
                
                if (\$signature) {{
                    # Чтение тела запроса
                    \$reader = New-Object System.IO.StreamReader(\$request.InputStream, \$request.ContentEncoding)
                    \$body = \$reader.ReadToEnd()
                    \$reader.Close()
                    
                    # Вычисление хеша
                    \$hmacsha1 = New-Object System.Security.Cryptography.HMACSHA1
                    \$hmacsha1.Key = [System.Text.Encoding]::ASCII.GetBytes(\$secretToken)
                    \$hash = "sha1=" + [BitConverter]::ToString(\$hmacsha1.ComputeHash([System.Text.Encoding]::ASCII.GetBytes(\$body))).Replace("-", "").ToLower()
                    
                    if (\$hash -eq \$signature) {{
                        \$isValid = \$true
                    }}
                }}
                
                if (\$isValid) {{
                    # Запуск скрипта деплоя
                    Start-Process powershell -ArgumentList "-File \`"\$deployScriptPath\`"" -NoNewWindow
                    
                    # Отправка ответа
                    \$responseText = "Запущен процесс деплоя"
                    \$buffer = [System.Text.Encoding]::UTF8.GetBytes(\$responseText)
                    \$response.ContentLength64 = \$buffer.Length
                    \$response.OutputStream.Write(\$buffer, 0, \$buffer.Length)
                }} else {{
                    # Отправка ошибки аутентификации
                    \$response.StatusCode = 401
                    \$responseText = "Неверная подпись"
                    \$buffer = [System.Text.Encoding]::UTF8.GetBytes(\$responseText)
                    \$response.ContentLength64 = \$buffer.Length
                    \$response.OutputStream.Write(\$buffer, 0, \$buffer.Length)
                }}
            }} else {{
                # Метод не поддерживается
                \$response.StatusCode = 405
            }}
        }} else {{
            # Путь не найден
            \$response.StatusCode = 404
        }}
        
        \$response.Close()
    }}
}} finally {{
    \$listener.Stop()
}}
"@

Set-Content -Path "$REPO_PATH\scripts\webhook_server.ps1" -Value $webhookServerScript

# Создание задачи в планировщике задач для автоматического запуска webhook сервера
$taskName = "WebhookServer"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$REPO_PATH\scripts\webhook_server.ps1`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Удаление задачи, если она уже существует
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Регистрация новой задачи
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings

# Запуск задачи
Start-ScheduledTask -TaskName $taskName

# Запуск ngrok для создания туннеля
Start-Process -FilePath "ngrok" -ArgumentList "start webhook" -NoNewWindow

Write-ColorOutput Green "Webhook успешно настроен и запущен на порту $WEBHOOK_PORT"
Write-ColorOutput Yellow "Инструкции по настройке webhook в GitHub/GitLab:"
Write-ColorOutput Yellow "1. Перейдите в настройки репозитория -> Webhooks -> Add webhook"
Write-ColorOutput Yellow "2. Получите URL туннеля ngrok из веб-интерфейса ngrok (http://localhost:4040)"
Write-ColorOutput Yellow "3. Укажите URL: [URL_NGROK]/hooks/deploy-telegram-bot"
Write-ColorOutput Yellow "4. Укажите Content type: application/json"
Write-ColorOutput Yellow "5. Укажите Secret: $SECRET_TOKEN"
Write-ColorOutput Yellow "6. Выберите события: Push events"
Write-ColorOutput Yellow "7. Сохраните webhook"