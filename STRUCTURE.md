# Структура проекта PlayerokCardinal

## Основные файлы

### Точки входа
- `main.py` - Главный файл запуска
- `Setup.bat` - Установка зависимостей (Windows)
- `Start.bat` - Запуск бота (Windows)
- `install-poc.sh` - Автоматическая установка (Linux)

### Конфигурация
- `first_setup.py` - Первичная настройка при первом запуске
- `requirements.txt` - Python зависимости
- `PlayerokCardinal@.service` - Systemd service для Linux

### Основная логика
- `cardinal.py` - Ядро бота, главный класс Cardinal
- `handlers.py` - Обработчики событий (сообщения, заказы)

## Директории

### PlayerokAPI/
API для работы с Playerok:
- `account.py` - Работа с аккаунтом
- `types.py` - Типы данных
- `parser.py` - Парсинг HTML
- `enums.py` - Перечисления
- `exceptions.py` - Исключения
- `misc.py` - Вспомогательные функции
- `listener/` - Прослушивание событий
  - `listener.py` - Основной слушатель
  - `events.py` - События

### Utils/
Утилиты и вспомогательные функции:
- `cardinal_tools.py` - Инструменты (прокси, blacklist, пароли)
- `config_loader.py` - Загрузка и валидация конфигов
- `exceptions.py` - Пользовательские исключения
- `logger.py` - Настройка логирования

### tg_bot/
Telegram бот для управления:
- `bot.py` - Основной класс Telegram бота

### configs/
Конфигурационные файлы (создаются автоматически):
- `_main.cfg` - Основной конфиг (создается при первом запуске)
- `auto_response.cfg` - Автоответчик
- `auto_delivery.cfg` - Автовыдача

### logs/
Логи работы бота (создаются автоматически):
- `log.log` - Основной лог файл

### storage/
Хранилище данных:
- `cache/` - Кэш (blacklist, и т.д.)
- `products/` - Товары для автовыдачи

### plugins/
Плагины для расширения функционала

## Особенности

### Без комментариев
Все файлы созданы без комментариев и документации, только чистый код.

### Linux поддержка
- Автоматический установочный скрипт `install-poc.sh`
- Systemd service для запуска как демон
- Поддержка Ubuntu 20.04+ и Debian 11+
- Python 3.11/3.12

### Windows поддержка
- Простые .bat файлы для установки и запуска
- Работает из коробки

### Безопасность
- Хеширование паролей с bcrypt
- Systemd service с ограничениями безопасности
- Поддержка прокси

## Запуск

### Windows
```bash
Setup.bat  # первый раз
Start.bat  # каждый раз
```

### Linux
```bash
sudo ./install-poc.sh
sudo systemctl start PlayerokCardinal@username
```

## Автор
[@KaDerix](https://github.com/KITUSTTT)

