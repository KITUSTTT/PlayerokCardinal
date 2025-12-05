# ⚡ Быстрый старт PlayerokCardinal

## 🐧 Linux (Ubuntu/Debian)

### 1. Скачай и запусти установку:

```bash
wget https://raw.githubusercontent.com/KITUSTTT/PlayerokCardinal/main/install-poc.sh
chmod +x install-poc.sh
sudo ./install-poc.sh
```

### 2. При установке введи:

- **Имя пользователя** для бота (например: `poc`)

### 3. После установки бот запросит:

✅ **Token Playerok** (JWT токен из Cookie)
   - [Как получить Token →](GET_TOKEN.md)
   - Пример: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi...`

✅ **User Agent** (нажми Enter для пропуска)
   - Или узнай на: https://whatmyuseragent.com

✅ **Telegram Bot Token** (от @BotFather)
   - Пример: `7257913369:AAG2KjLL3-zvvfSQFSVhaTb4w7tR2iXsJXM`
   - Username должен начинаться с `playerok`

✅ **Пароль для бота** (8+ символов)
   - Заглавные + строчные буквы + цифры

✅ **Прокси** (нажми Enter для пропуска)
   - Формат: `login:password@ip:port` или `ip:port`

### 4. Готово! 🎉

После настройки бот запустится автоматически.

```bash
# Проверь статус
sudo systemctl status PlayerokCardinal@poc

# Посмотри логи
sudo journalctl -u PlayerokCardinal@poc -f
```

---

## 🪟 Windows

### 1. Скачай проект:

```
Code → Download ZIP
```

### 2. Распакуй и запусти:

```cmd
Setup.bat    # Установит зависимости
Start.bat    # Запустит бота
```

### 3. Введи те же данные что и на Linux

✅ Token Playerok  
✅ User Agent (опционально)  
✅ Telegram Bot Token  
✅ Пароль  
✅ Прокси (опционально)  

### 4. Готово! 🎉

Бот запустится в консоли.

---

## 🆘 Не спрашивает данные?

Если бот сразу завершается или не спрашивает данные:

### На Linux:

```bash
# Перейди в папку бота
cd /home/poc/PlayerokCardinal

# Удали старый конфиг если есть
sudo -u poc rm -f configs/_main.cfg

# Запусти вручную
sudo -u poc /home/poc/pyvenv/bin/python main.py
```

### На Windows:

```cmd
# Удали configs/_main.cfg если есть
del configs\_main.cfg

# Запусти заново
python main.py
```

---

## 📞 Нужна помощь?

- **Telegram**: [@KaDerix](https://t.me/KaDerix)
- **GitHub Issues**: [Сообщить о проблеме](https://github.com/KITUSTTT/PlayerokCardinal/issues)

