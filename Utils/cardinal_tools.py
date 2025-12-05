import bcrypt
import requests
import psutil
import json
import sys
import os
import re
import logging

logger = logging.getLogger("POC.cardinal_tools")

def count_products(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        products = f.read()
    products = [p for p in products.split("\n") if p]
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
    logger.info("Проверяю прокси...")
    try:
        response = requests.get("https://api.ipify.org/", proxies=proxy, timeout=10)
    except:
        logger.error("Не удалось подключиться к прокси.")
        logger.debug("TRACEBACK", exc_info=True)
        return False
    logger.info(f"Прокси работает. IP: {response.content.decode()}")
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

def set_console_title(title: str):
    if sys.platform == "win32":
        os.system(f"title {title}")
    else:
        sys.stdout.write(f"\x1b]2;{title}\x07")


