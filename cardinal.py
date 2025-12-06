from __future__ import annotations
from typing import TYPE_CHECKING
from threading import Thread

if TYPE_CHECKING:
    from configparser import ConfigParser

import PlayerokAPI
from PlayerokAPI.listener.listener import EventListener
from PlayerokAPI.listener.events import *
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
                from locales.localizer import Localizer
                localizer = Localizer()
                _ = localizer.translate
                logger.info(_("crd_proxy_detected"))
                logger.info(_("crd_checking_proxy"))
                ip, port = self.MAIN_CFG["Proxy"]["ip"], self.MAIN_CFG["Proxy"]["port"]
                login, password = self.MAIN_CFG["Proxy"]["login"], self.MAIN_CFG["Proxy"]["password"]
                proxy_str = f"{f'{login}:{password}@' if login and password else ''}{ip}:{port}"
                self.proxy = {
                    "http": f"http://{proxy_str}",
                    "https": f"http://{proxy_str}"
                }
                
                if self.MAIN_CFG["Proxy"].get("check") == "1":
                    if not cardinal_tools.check_proxy(self.proxy):
                        logger.error(_("crd_proxy_err"))
                        sys.exit()
                    else:
                        import requests
                        try:
                            response = requests.get("https://api.ipify.org?format=json", proxies=self.proxy, timeout=10)
                            ip_address = response.json().get("ip", "unknown")
                            logger.info(_("crd_proxy_success", ip_address))
                        except:
                            pass

        self.account = PlayerokAPI.Account(
            token=self.MAIN_CFG["Playerok"]["token"],
            user_agent=self.MAIN_CFG["Playerok"]["user_agent"],
            proxy=self.proxy
        )
        
        self.listener: EventListener | None = None
        self.telegram: "tg_bot.bot.TGBot" | None = None
        
        self.running = False
        self.run_id = 0
        self.start_time = int(time.time())
        self.blacklist = cardinal_tools.load_blacklist()
        
        self.autoresponse_enabled = self.MAIN_CFG["Playerok"].get("autoResponse") == "1"
        self.autodelivery_enabled = self.MAIN_CFG["Playerok"].get("autoDelivery") == "1"
        self.autorestore_enabled = self.MAIN_CFG["Playerok"].get("autoRestore") == "1"
        
        self.new_message_handlers = []
        self.new_order_handlers = []
        self.chat_initialized_handlers = []
        self.new_deal_handlers = []
        self.item_paid_handlers = []
        self.item_sent_handlers = []
        self.deal_confirmed_handlers = []

    def __init_account(self):
        """Инициализирует аккаунт"""
        from locales.localizer import Localizer
        localizer = Localizer()
        _ = localizer.translate
        
        while True:
            try:
                profile = self.account.get()
                logger.info(f"$GREENУспешно авторизован как: $YELLOW{profile.username}$RESET")
                cardinal_tools.set_console_title(f"Playerok Cardinal - {profile.username}")
                break
            except TimeoutError:
                logger.error(_("crd_acc_get_timeout_err"))
            except Exception as e:
                logger.error(f"$REDОшибка при авторизации: $YELLOW{e}$RESET")
                logger.debug("TRACEBACK", exc_info=True)
            logger.warning(_("crd_try_again_in_n_secs", 2))
            time.sleep(2)

    def __init_telegram(self):
        """Инициализирует Telegram бота"""
        if self.MAIN_CFG["Telegram"].get("enabled") == "1":
            from tg_bot import bot
            self.telegram = bot.TGBot(self)
            self.telegram.init()
            Thread(target=self.telegram.run, daemon=True).start()

    def init(self):
        from locales.localizer import Localizer
        localizer = Localizer()
        _ = localizer.translate
        
        logger.info("$CYANИнициализация Cardinal...$RESET")
        
        handlers.register_handlers(self)
        
        if self.MAIN_CFG["Telegram"].get("enabled") == "1":
            self.__init_telegram()
            # Импортируем и регистрируем обработчики Telegram
            try:
                from tg_bot import auto_response_cp, auto_delivery_cp, config_loader_cp, templates_cp, plugins_cp, \
                                   file_uploader, authorized_users_cp, proxy_cp, default_cp
                for module in [auto_response_cp, auto_delivery_cp, config_loader_cp, templates_cp, plugins_cp,
                               file_uploader, authorized_users_cp, proxy_cp, default_cp]:
                    try:
                        if hasattr(module, 'init'):
                            module.init(self)
                    except Exception as e:
                        logger.error(f"$REDОшибка при инициализации модуля $YELLOW{module.__name__}$RESET: $YELLOW{e}$RESET")
                        logger.debug("TRACEBACK", exc_info=True)
            except Exception as e:
                logger.warning(f"$YELLOWОшибка при загрузке Telegram модулей: $YELLOW{e}$RESET")
                logger.debug("TRACEBACK", exc_info=True)
        
        self.__init_account()
        self.listener = EventListener(self.account)
        
        logger.info("$GREENCardinal инициализирован успешно!$RESET")
        return self

    def process_events(self):
        """Обрабатывает события от EventListener"""
        instance_id = self.run_id
        events_handlers = {
            PlayerokAPI.enums.EventTypes.CHAT_INITIALIZED: self.chat_initialized_handlers,
            PlayerokAPI.enums.EventTypes.NEW_MESSAGE: self.new_message_handlers,
            PlayerokAPI.enums.EventTypes.NEW_DEAL: self.new_order_handlers,
            PlayerokAPI.enums.EventTypes.ITEM_PAID: self.item_paid_handlers,
            PlayerokAPI.enums.EventTypes.ITEM_SENT: self.item_sent_handlers,
            PlayerokAPI.enums.EventTypes.DEAL_CONFIRMED: self.deal_confirmed_handlers,
        }
        
        requests_delay = int(self.MAIN_CFG["Other"].get("requestsDelay", "4"))
        
        for event in self.listener.listen(requests_delay=requests_delay):
            if instance_id != self.run_id:
                break
            
            event_type = event.type
            if event_type in events_handlers:
                for handler in events_handlers[event_type]:
                    try:
                        handler(self, event)
                    except Exception as e:
                        logger.error(f"$REDОшибка в обработчике события $YELLOW{event_type}$RESET: $YELLOW{e}$RESET")
                        logger.debug("TRACEBACK", exc_info=True)

    def run(self):
        logger.info("$CYANЗапуск Cardinal...$RESET")
        self.run_id += 1
        self.running = True
        self.start_time = int(time.time())
        
        try:
            self.process_events()
        except KeyboardInterrupt:
            logger.info("$YELLOWПолучен сигнал остановки...$RESET")
            self.running = False
        except Exception as e:
            logger.error(f"$REDОшибка при обработке событий: $YELLOW{e}$RESET")
            logger.debug("TRACEBACK", exc_info=True)
            self.running = False

    @property
    def block_tg_login(self) -> bool:
        return self.MAIN_CFG["Telegram"].getboolean("blockLogin")

    def send_message(self, chat_id: int, text: str, chat_name: str = ""):
        """Отправляет сообщение в чат"""
        try:
            logger.info(f"$CYANОтправка сообщения в чат $YELLOW{chat_name} (ID: {chat_id})$RESET: $CYAN{text[:50]}...$RESET")
            self.account.send_message(str(chat_id), text)
            logger.info(f"$GREENСообщение отправлено в чат $YELLOW{chat_name}$RESET")
            return True
        except Exception as e:
            logger.error(f"$REDОшибка при отправке сообщения: $YELLOW{e}$RESET")
            logger.debug("TRACEBACK", exc_info=True)
            return False
