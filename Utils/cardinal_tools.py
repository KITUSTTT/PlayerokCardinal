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

def set_console_title(title: str):
    if sys.platform == "win32":
        os.system(f"title {title}")
    else:
        sys.stdout.write(f"\x1b]2;{title}\x07")

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

