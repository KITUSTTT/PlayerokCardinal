from __future__ import annotations
from typing import TYPE_CHECKING

import bcrypt
import requests
import psutil
import json
import sys
import os
import re
import logging
import time
import itertools
from datetime import datetime

if TYPE_CHECKING:
    from cardinal import Cardinal

import PlayerokAPI.types
import Utils.exceptions

logger = logging.getLogger("POC.cardinal_tools")

def count_products(path: str) -> int:
    """
    Считает кол-во товара в указанном файле.

    :param path: путь до файла с товарами.

    :return: кол-во товара в указанном файле.
    """
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        products = f.read()
    products = products.split("\n")
    products = list(itertools.filterfalse(lambda el: not el, products))
    return len(products)

def cache_blacklist(blacklist: list[str]) -> None:
    if not os.path.exists("storage/cache"):
        os.makedirs("storage/cache")
    with open("storage/cache/blacklist.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(blacklist, indent=4))

def load_blacklist() -> list[str]:
    if not os.path.exists("storage/cache/blacklist.json"):
        return []
    with open("storage/cache/blacklist.json", "r", encoding="utf-8") as f:
        blacklist = f.read()
        try:
            blacklist = json.loads(blacklist)
        except json.decoder.JSONDecodeError:
            return []
        return blacklist

def check_proxy(proxy: dict) -> bool:
    from locales.localizer import Localizer
    localizer = Localizer()
    _ = localizer.translate
    
    logger.info(_("crd_checking_proxy"))
    try:
        response = requests.get("https://api.ipify.org?format=json", proxies=proxy, timeout=10)
        ip_address = response.json().get("ip", response.content.decode())
    except:
        logger.error(_("crd_proxy_err"))
        logger.debug("TRACEBACK", exc_info=True)
        return False
    logger.info(_("crd_proxy_success", ip_address))
    return True

def validate_proxy(proxy: str):
    pattern = r"^((?P<login>[^:]+):(?P<password>[^@]+)@)?(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<port>\d+)$"
    result = re.fullmatch(pattern, proxy)
    if not result:
        raise ValueError("Неверный формат прокси.")
    login = result.group("login") or ""
    password = result.group("password") or ""
    ip = result.group("ip")
    port = result.group("port")
    return login, password, ip, port

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def set_console_title(title: str) -> None:
    """
    Изменяет название консоли для Windows.
    """
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
    except:
        logger.warning("Произошла ошибка при изменении названия консоли")
        logger.debug("TRACEBACK", exc_info=True)

def cache_proxy_dict(proxy_dict: dict[int, str]) -> None:
    """
    Кэширует список прокси.
    
    :param proxy_dict: список прокси.
    """
    if not os.path.exists("storage/cache"):
        os.makedirs("storage/cache")
    
    with open("storage/cache/proxy_dict.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(proxy_dict, indent=4))

def load_proxy_dict() -> dict[int, str]:
    """
    Загружает список прокси.
    
    :return: список прокси.
    """
    if not os.path.exists("storage/cache/proxy_dict.json"):
        return {}
    
    with open("storage/cache/proxy_dict.json", "r", encoding="utf-8") as f:
        proxy = f.read()
        
        try:
            proxy = json.loads(proxy)
            proxy = {int(k): v for k, v in proxy.items()}
        except json.decoder.JSONDecodeError:
            return {}
        return proxy


def cache_disabled_plugins(disabled_plugins: list[str]) -> None:
    """
    Кэширует UUID отключенных плагинов.

    :param disabled_plugins: список UUID отключенных плагинов.
    """
    if not os.path.exists("storage/cache"):
        os.makedirs("storage/cache")

    with open("storage/cache/disabled_plugins.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(disabled_plugins))


def load_disabled_plugins() -> list[str]:
    """
    Загружает список UUID отключенных плагинов из кэша.

    :return: список UUID отключенных плагинов.
    """
    if not os.path.exists("storage/cache/disabled_plugins.json"):
        return []

    with open("storage/cache/disabled_plugins.json", "r", encoding="utf-8") as f:
        try:
            return json.loads(f.read())
        except json.decoder.JSONDecodeError:
            return []


def cache_old_users(old_users: dict[int, float]):
    """
    Сохраняет в кэш список пользователей, которые уже писали на аккаунт.
    """
    if not os.path.exists("storage/cache"):
        os.makedirs("storage/cache")
    with open(f"storage/cache/old_users.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(old_users, ensure_ascii=False))


def load_old_users(greetings_cooldown: float) -> dict[int, float]:
    """
    Загружает из кэша список пользователей, которые уже писали на аккаунт.

    :return: список ID чатов.
    """
    if not os.path.exists(f"storage/cache/old_users.json"):
        return dict()
    with open(f"storage/cache/old_users.json", "r", encoding="utf-8") as f:
        users = f.read()
    try:
        users = json.loads(users)
    except json.decoder.JSONDecodeError:
        return dict()
    # todo убрать позже, конвертация для старых версий кардинала
    if type(users) == list:
        users = {user: time.time() for user in users}
    else:
        users = {int(user): time_ for user, time_ in users.items() if
                 time.time() - time_ < greetings_cooldown * 24 * 60 * 60}
    cache_old_users(users)
    return users


def create_greeting_text(cardinal: Cardinal) -> str:
    """
    Генерирует приветствие для вывода в консоль после загрузки данных о пользователе.
    """
    account = cardinal.account
    balance = cardinal.balance
    current_time = datetime.now()
    if current_time.hour < 4:
        greetings = "Какая прекрасная ночь"  # locale
    elif current_time.hour < 12:
        greetings = "Доброе утро"
    elif current_time.hour < 17:
        greetings = "Добрый день"
    else:
        greetings = "Добрый вечер"

    # Получаем активные сделки
    active_sales = 0
    try:
        if hasattr(account, 'profile') and account.profile and hasattr(account.profile, 'stats'):
            if hasattr(account.profile.stats, 'deals') and account.profile.stats.deals:
                if hasattr(account.profile.stats.deals, 'incoming') and account.profile.stats.deals.incoming:
                    active_sales = getattr(account.profile.stats.deals.incoming, 'total', 0)
    except:
        pass
    
    # Форматируем баланс (баланс уже в рублях, не делим на 100)
    balance_rub = balance.value if balance.value else 0
    
    lines = [
        f"* {greetings}, $CYAN{account.username}.",
        f"* Ваш ID: $YELLOW{account.id}.",
        f"* Ваш текущий баланс: $CYAN{balance_rub:.2f} RUB",
        f"* Текущие незавершенные сделки: $YELLOW{active_sales}.",
        f"* Удачной торговли!"
    ]

    length = 60
    greetings_text = f"\n{'-' * length}\n"
    for line in lines:
        greetings_text += line + " " * (length - len(
            line.replace("$CYAN", "").replace("$YELLOW", "").replace("$MAGENTA", "").replace("$RESET",
                                                                                             "")) - 1) + "$RESET*\n"
    greetings_text += f"{'-' * length}\n"
    return greetings_text


def time_to_str(time_: int):
    """
    Конвертирует число в строку формата "Хд Хч Хмин Хсек"

    :param time_: число для конвертации.

    :return: строку-время.
    """
    days = time_ // 86400
    hours = (time_ - days * 86400) // 3600
    minutes = (time_ - days * 86400 - hours * 3600) // 60
    seconds = time_ - days * 86400 - hours * 3600 - minutes * 60

    if not any([days, hours, minutes, seconds]):  # locale
        return "0 сек"
    time_str = ""
    if days:
        time_str += f"{days}д"
    if hours:
        time_str += f" {hours}ч"
    if minutes:
        time_str += f" {minutes}мин"
    if seconds:
        time_str += f" {seconds}сек"
    return time_str.strip()


def get_month_name(month_number: int) -> str:
    """
    Возвращает название месяца в родительном падеже.

    :param month_number: номер месяца.

    :return: название месяца в родительном падеже.
    """
    months = [
        "Января", "Февраля", "Марта",
        "Апреля", "Мая", "Июня",
        "Июля", "Августа", "Сентября",
        "Октября", "Ноября", "Декабря"
    ]  # todo локализация
    if month_number > len(months):
        return months[0]
    return months[month_number - 1]


def get_products(path: str, amount: int = 1) -> list[list[str] | int] | None:
    """
    Берет из товарного файла товар/-ы, удаляет их из товарного файла.

    :param path: путь до файла с товарами.
    :param amount: кол-во товара.

    :return: [[Товар/-ы], оставшееся кол-во товара]
    """
    with open(path, "r", encoding="utf-8") as f:
        products = f.read()

    products = products.split("\n")

    # Убираем пустые элементы
    products = list(itertools.filterfalse(lambda el: not el, products))

    if not products:
        raise Utils.exceptions.NoProductsError(path)

    elif len(products) < amount:
        raise Utils.exceptions.NotEnoughProductsError(path, len(products), amount)

    got_products = products[:amount]
    save_products = products[amount:]
    amount = len(save_products)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(save_products))

    return [got_products, amount]


def add_products(path: str, products: list[str], at_zero_position=False):
    """
    Добавляет товары в файл с товарами.

    :param path: путь до файла с товарами.
    :param products: товары.
    :param at_zero_position: добавить товары в начало товарного файла.
    """
    if not at_zero_position:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(products))
    else:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(products) + "\n" + text)


def safe_text(text: str):
    return "⁣".join(text)


def format_msg_text(text: str, obj: PlayerokAPI.types.ChatMessage | PlayerokAPI.types.Chat) -> str:
    """
    Форматирует текст, подставляя значения переменных, доступных для MessageEvent.

    :param text: текст для форматирования.
    :param obj: экземпляр types.ChatMessage или types.Chat.

    :return: форматированый текст.
    """
    date_obj = datetime.now()
    month_name = get_month_name(date_obj.month)
    date = date_obj.strftime("%d.%m.%Y")
    str_date = f"{date_obj.day} {month_name}"
    str_full_date = str_date + f" {date_obj.year} года"  # locale

    time_ = date_obj.strftime("%H:%M")
    time_full = date_obj.strftime("%H:%M:%S")

    if isinstance(obj, PlayerokAPI.types.ChatMessage):
        username = obj.user.username if hasattr(obj.user, 'username') else str(obj.user.id)
        chat_name = obj.chat.id if hasattr(obj, 'chat') and obj.chat else ""
        chat_id = obj.chat.id if hasattr(obj, 'chat') and obj.chat else ""
    else:  # Chat
        username = obj.users[0].username if obj.users and hasattr(obj.users[0], 'username') else str(obj.users[0].id) if obj.users else ""
        chat_name = obj.id
        chat_id = obj.id

    variables = {
        "$full_date_text": str_full_date,
        "$date_text": str_date,
        "$date": date,
        "$time": time_,
        "$full_time": time_full,
        "$username": safe_text(username),
        "$message_text": str(obj),
        "$chat_id": str(chat_id),
        "$chat_name": safe_text(chat_name)
    }

    for var in variables:
        text = text.replace(var, variables[var])
    return text


def format_order_text(text: str, order: PlayerokAPI.types.ItemDeal) -> str:
    """
    Форматирует текст, подставляя значения переменных, доступных для Order.

    :param text: текст для форматирования.
    :param order: экземпляр ItemDeal.

    :return: форматированый текст.
    """
    date_obj = datetime.now()
    month_name = get_month_name(date_obj.month)
    date = date_obj.strftime("%d.%m.%Y")
    str_date = f"{date_obj.day} {month_name}"
    str_full_date = str_date + f" {date_obj.year} года"  # locale
    time_ = date_obj.strftime("%H:%M")
    time_full = date_obj.strftime("%H:%M:%S")
    game = subcategory_fullname = subcategory = ""
    try:
        if hasattr(order.item, 'category') and order.item.category:
            subcategory_fullname = order.item.category.name if hasattr(order.item.category, 'name') else ""
            game = order.item.category.game.name if hasattr(order.item.category, 'game') and order.item.category.game else ""
            subcategory = order.item.category.name if hasattr(order.item.category, 'name') else ""
    except:
        logger.warning("Произошла ошибка при парсинге игры из заказа")  # locale
        logger.debug("TRACEBACK", exc_info=True)
    description = order.item.name if hasattr(order.item, 'name') else ""
    params = order.props if hasattr(order, 'props') and order.props else ""
    username = order.user.username if hasattr(order.user, 'username') else str(order.user.id)
    variables = {
        "$full_date_text": str_full_date,
        "$date_text": str_date,
        "$date": date,
        "$time": time_,
        "$full_time": time_full,
        "$username": safe_text(username),
        "$order_desc_and_params": f"{description}, {params}" if description and params else f"{description}{params}",
        "$order_desc_or_params": description if description else params,
        "$order_desc": description,
        "$order_title": description,
        "$order_params": params,
        "$order_id": order.id,
        "$order_link": f"https://playerok.com/deals/{order.id}/",
        "$category_fullname": subcategory_fullname,
        "$category": subcategory,
        "$game": game
    }

    for var in variables:
        text = text.replace(var, variables[var])
    return text


def restart_program():
    """
    Полный перезапуск POC.
    """
    python = sys.executable
    os.execl(python, python, *sys.argv)
    try:
        process = psutil.Process()
        for handler in process.open_files():
            os.close(handler.fd)
        for handler in process.connections():
            os.close(handler.fd)
    except:
        pass


def shut_down():
    """
    Полное отключение POC.
    """
    try:
        process = psutil.Process()
        process.terminate()
    except:
        pass

