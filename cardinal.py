from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from configparser import ConfigParser

import PlayerokAPI
from Utils import cardinal_tools
import handlers
import logging
import time
import sys

logger = logging.getLogger("POC")

def get_cardinal() -> None | Cardinal:
    if hasattr(Cardinal, "instance"):
        return getattr(Cardinal, "instance")

class Cardinal(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(Cardinal, cls).__new__(cls)
        return getattr(cls, "instance")

    def __init__(self, main_config: ConfigParser,
                 auto_delivery_config: list,
                 auto_response_config: dict,
                 raw_auto_response_config: ConfigParser,
                 version: str):
        self.VERSION = version
        
        self.MAIN_CFG = main_config
        self.AD_CFG = auto_delivery_config
        self.AR_CFG = auto_response_config
        self.RAW_AR_CFG = raw_auto_response_config
        
        self.proxy = {}
        if self.MAIN_CFG["Proxy"].get("enable") == "1":
            if self.MAIN_CFG["Proxy"]["ip"] and self.MAIN_CFG["Proxy"]["port"].isnumeric():
                logger.info("Обнаружен прокси...")
                ip, port = self.MAIN_CFG["Proxy"]["ip"], self.MAIN_CFG["Proxy"]["port"]
                login, password = self.MAIN_CFG["Proxy"]["login"], self.MAIN_CFG["Proxy"]["password"]
                proxy_str = f"{f'{login}:{password}@' if login and password else ''}{ip}:{port}"
                self.proxy = {
                    "http": f"http://{proxy_str}",
                    "https": f"http://{proxy_str}"
                }
                
                if self.MAIN_CFG["Proxy"].get("check") == "1" and not cardinal_tools.check_proxy(self.proxy):
                    sys.exit()

        self.account = PlayerokAPI.Account(
            token=self.MAIN_CFG["Playerok"]["token"],
            user_agent=self.MAIN_CFG["Playerok"]["user_agent"],
            proxy=self.proxy
        )
        
        self.running = False
        self.start_time = int(time.time())
        self.blacklist = cardinal_tools.load_blacklist()
        
        self.autoresponse_enabled = self.MAIN_CFG["Playerok"].get("autoResponse") == "1"
        self.autodelivery_enabled = self.MAIN_CFG["Playerok"].get("autoDelivery") == "1"
        self.autorestore_enabled = self.MAIN_CFG["Playerok"].get("autoRestore") == "1"
        
        self.new_message_handlers = []
        self.new_order_handlers = []

    def init(self):
        logger.info("Инициализация Cardinal...")
        
        try:
            profile = self.account.get()
            logger.info(f"Успешно авторизован как: {profile.username}")
        except Exception as e:
            logger.error(f"Ошибка при авторизации: {e}")
            sys.exit(1)
        
        handlers.register_handlers(self)
        
        logger.info("Cardinal инициализирован успешно!")
        return self

    def run(self):
        logger.info("Запуск Cardinal...")
        self.running = True
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки...")
            self.running = False

    def send_message(self, chat_id: int, text: str, chat_name: str = ""):
        try:
            logger.info(f"Отправка сообщения в чат {chat_name} ({chat_id})")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False


