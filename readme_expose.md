# Тоннель в интернет для локального сайта 

## Об expose

[Expose](https://expose.dev/) — это туннельное приложение, которое позволяет вам делиться вашими локальными сайтами и приложениями с 
другими в
Интернете и получать вебхуки во время разработки. 

## Регистрация
Регистрация обычная через почту/пароль или через аккаунт на Github.

## Доступ
После аутенфикации на сайте, на главной странице будет отображаться ваш собственный токен, который используется для 
подключения через CLI

##  Установка с помощью Docker

### 1. Создайте папку репозитория:
    ```bash
   mkdir C:\Users\<User>\expose
   cd expose
    ```
### 2. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/beyondcode/expose.git
    ```

### 3. Собери Docker-образ:
    ```bash
    docker build -t expose .
    ```
### 4. Добавь скрипт для запуска контейнера. 
   1. Создай файл expose.ps1
   ```bash
   param(
      [Parameter(ValueFromRemainingArguments = $true)]
       [string[]]$Args
   )

   $configPath = Join-Path $env:USERPROFILE ".expose\config.json"

   if (!(Test-Path $configPath) -and ($Args.Count -eq 0 -or $Args[0] -ne "token")) {
      Write-Host "❗ Токен не найден. Пожалуйста, сначала укажите токен:"
      Write-Host "Пример: .\expose.ps1 token <ваш_токен>"
       exit
   }

   if ($Args.Count -gt 0 -and $Args[0] -eq "share") {
      docker run --rm -it `
         -v "${PWD}:/app" `
         -v "${env:USERPROFILE}/.expose:/root/.expose" `
         -w /app `
         expose `
         @Args
   }
   elseif ($Args.Count -gt 1 -and $Args[0] -eq "token") {
      docker run --rm -it `
        -v "${env:USERPROFILE}/.expose:/root/.expose" `
        expose `
         @Args
   }
   else {
       Write-Host "❗ Укажите команду: token или share"
       Write-Host "Пример для токена: .\expose.ps1 token <ваш_токен>"
       Write-Host "Пример для запуска: .\expose.ps1 share http://127.0.0.1:8080"
   }
   ```

   2. В PATH добавь путь к папке, где находится expose.ps1
   
   - Нажми Win + R → введи SystemPropertiesAdvanced → Enter.
   - Нажми "Переменные среды".
   - В нижнем окне найди Path → Изменить → Добавить путь к папке, где находится expose.ps1.
   - Подтверди всё нажатием OK.

   3. Разреши запуск PowerShell-скриптов
      ```bash
      Set-ExecutionPolicy RemoteSigned
      ```
      Выбери Y для подтверждения.

### 4. Создай папку для хранения твоей конфигурации
   ```bash
   mkdir $env:USERPROFILE\.expose
   ```
## Запуск контейнера expose
   ```bash
  .\expose.ps1 token <token>
  .\expose.ps1 share http://host.docker.internal:4040
   ```
---
### p.s.
Тоннель работает 1 час, потом надо снова перезапускать
