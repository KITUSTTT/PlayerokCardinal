from __future__ import annotations
from typing import TYPE_CHECKING, Callable
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
import os
import importlib.util
from types import ModuleType
from uuid import UUID

logger = logging.getLogger("POC")

def get_cardinal() -> None | Cardinal:
    if hasattr(Cardinal, "instance"):
        return getattr(Cardinal, "instance")


class PluginData:
    """
    Класс, описывающий плагин.
    """

    def __init__(self, name: str, version: str, desc: str, credentials: str, uuid: str,
                 path: str, plugin: ModuleType, settings_page: bool, delete_handler: Callable | None, enabled: bool):
        """
        :param name: название плагина.
        :param version: версия плагина.
        :param desc: описание плагина.
        :param credentials: авторы плагина.
        :param uuid: UUID плагина.
        :param path: путь до плагина.
        :param plugin: экземпляр плагина как модуля.
        :param settings_page: есть ли страница настроек у плагина.
        :param delete_handler: хэндлер, привязанный к удалению плагина.
        :param enabled: включен ли плагин.
        """
        self.name = name
        self.version = version
        self.description = desc
        self.credits = credentials
        self.uuid = uuid

        self.path = path
        self.plugin = plugin
        self.settings_page = settings_page
        self.commands = {}
        self.delete_handler = delete_handler
        self.enabled = enabled


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
        
        self.proxy = None
        self.proxy_dict = {}  # Для проверки прокси через requests
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
                # Словарь для проверки прокси через requests
                self.proxy_dict = {
                    "http": f"http://{proxy_str}",
                    "https": f"http://{proxy_str}"
                }
                # Строка для PlayerokAPI.Account
                self.proxy = proxy_str
                
                if self.MAIN_CFG["Proxy"].get("check") == "1":
                    if not cardinal_tools.check_proxy(self.proxy_dict):
                        logger.error(_("crd_proxy_err"))
                        sys.exit()
                    else:
                        import requests
                        try:
                            response = requests.get("https://api.ipify.org?format=json", proxies=self.proxy_dict, timeout=10)
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
        self.instance_id = id(self)  # ID экземпляра для проверки при выключении
        self.blacklist = cardinal_tools.load_blacklist()
        
        self.autoresponse_enabled = self.MAIN_CFG["Playerok"].get("autoResponse") == "1"
        self.autodelivery_enabled = self.MAIN_CFG["Playerok"].get("autoDelivery") == "1"
        self.autorestore_enabled = self.MAIN_CFG["Playerok"].get("autoRestore") == "1"
        
        # Хэндлеры
        self.pre_init_handlers = []
        self.post_init_handlers = []
        self.pre_start_handlers = []
        self.post_start_handlers = []
        self.pre_stop_handlers = []
        self.post_stop_handlers = []
        
        self.new_message_handlers = []
        self.new_order_handlers = []
        self.chat_initialized_handlers = []
        self.new_deal_handlers = []
        self.item_paid_handlers = []
        self.item_sent_handlers = []
        self.deal_confirmed_handlers = []
        
        self.balance = None
        
        # Плагины
        self.plugins: dict[str, PluginData] = {}
        self.disabled_plugins = cardinal_tools.load_disabled_plugins()
        
        # Хэндлеры для плагинов
        self.handler_bind_var_names = {
            "BIND_TO_PRE_INIT": self.pre_init_handlers,
            "BIND_TO_POST_INIT": self.post_init_handlers,
            "BIND_TO_PRE_START": self.pre_start_handlers,
            "BIND_TO_POST_START": self.post_start_handlers,
            "BIND_TO_PRE_STOP": self.pre_stop_handlers,
            "BIND_TO_POST_STOP": self.post_stop_handlers,
            "BIND_TO_NEW_MESSAGE": self.new_message_handlers,
            "BIND_TO_NEW_ORDER": self.new_order_handlers,
            "BIND_TO_CHAT_INITIALIZED": self.chat_initialized_handlers,
            "BIND_TO_NEW_DEAL": self.new_deal_handlers,
            "BIND_TO_ITEM_PAID": self.item_paid_handlers,
            "BIND_TO_ITEM_SENT": self.item_sent_handlers,
            "BIND_TO_DEAL_CONFIRMED": self.deal_confirmed_handlers,
        }

    def get_balance(self):
        """Получает баланс аккаунта"""
        try:
            # Получаем профиль аккаунта
            if hasattr(self.account, 'profile') and self.account.profile:
                if hasattr(self.account.profile, 'balance') and self.account.profile.balance:
                    return self.account.profile.balance
            # Если баланс не найден, обновляем данные аккаунта
            self.account.get()
            if hasattr(self.account, 'profile') and self.account.profile and hasattr(self.account.profile, 'balance'):
                return self.account.profile.balance
            # Создаем пустой баланс если не найден
            from PlayerokAPI.types import AccountBalance
            return AccountBalance(id="", value=0, frozen=0, available=0, withdrawable=0, pending_income=0)
        except Exception as e:
            logger.error(f"$REDОшибка при получении баланса: $YELLOW{e}$RESET")
            logger.debug("TRACEBACK", exc_info=True)
            from PlayerokAPI.types import AccountBalance
            return AccountBalance(id="", value=0, frozen=0, available=0, withdrawable=0, pending_income=0)

    def __init_account(self):
        """Инициализирует аккаунт"""
        from locales.localizer import Localizer
        localizer = Localizer()
        _ = localizer.translate
        
        while True:
            try:
                profile = self.account.get()
                self.balance = self.get_balance()
                greeting_text = cardinal_tools.create_greeting_text(self)
                cardinal_tools.set_console_title(f"Playerok Cardinal - {profile.username} ({profile.id})")
                for line in greeting_text.split("\n"):
                    logger.info(line)
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
                        # Регистрируем обработчики из модуля через BIND_TO_*
                        self.add_handlers_from_plugin(module)
                    except Exception as e:
                        logger.error(f"$REDОшибка при регистрации обработчиков модуля $YELLOW{module.__name__}$RESET: $YELLOW{e}$RESET")
                        logger.debug("TRACEBACK", exc_info=True)
                
                # Вызываем pre_init обработчики (они регистрируют callback handlers в telegram боте)
                self.run_handlers(self.pre_init_handlers, (self,))
            except Exception as e:
                logger.warning(f"$YELLOWОшибка при загрузке Telegram модулей: $YELLOW{e}$RESET")
                logger.debug("TRACEBACK", exc_info=True)
        
        self.__init_account()
        self.listener = EventListener(self.account)
        
        # Загружаем плагины
        self.load_plugins()
        self.add_handlers()
        
        logger.info("$GREENCardinal инициализирован успешно!$RESET")
        
        # Вызываем post_init_handlers с задержкой, чтобы бот успел отправить bot_started
        import time
        time.sleep(2)  # Даем время боту отправить сообщение bot_started и заполнить init_messages
        self.run_handlers(self.post_init_handlers, (self,))
        
        # Обновляем меню команд после загрузки плагинов и выполнения post_init_handlers
        # (чтобы команды из плагинов успели зарегистрироваться)
        if self.telegram:
            self.telegram.update_commands_menu()
        
        return self
    
    def run_handlers(self, handlers_list: list, args: tuple):
        """Вызывает список обработчиков с указанными аргументами"""
        for handler in handlers_list:
            try:
                plugin_uuid = getattr(handler, "plugin_uuid", None)
                if plugin_uuid is None or (plugin_uuid in self.plugins and self.plugins[plugin_uuid].enabled):
                    handler(*args)
            except Exception as e:
                logger.error(f"$REDОшибка в обработчике: $YELLOW{e}$RESET")
                logger.debug("TRACEBACK", exc_info=True)

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
        return self.MAIN_CFG["Telegram"].get("blockLogin", "0") == "1"
    
    @staticmethod
    def save_config(config: dict | ConfigParser, path: str):
        """Сохраняет конфиг в файл"""
        import configparser
        if isinstance(config, dict):
            # Если config это dict, создаем ConfigParser и заполняем его
            cfg = configparser.ConfigParser(delimiters=(":",), interpolation=None)
            cfg.optionxform = str
            for section_name, section_data in config.items():
                cfg.add_section(section_name)
                for key, value in section_data.items():
                    cfg.set(section_name, key, str(value))
            with open(path, "w", encoding="utf-8") as f:
                cfg.write(f)
        else:
            # Если config это ConfigParser, сохраняем как обычно
            with open(path, "w", encoding="utf-8") as f:
                config.write(f)

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
    
    @staticmethod
    def is_plugin(file: str) -> bool:
        """
        Есть ли "noplug" в начале файла плагина?

        :param file: файл плагина.
        """
        with open(f"plugins/{file}", "r", encoding="utf-8") as f:
            line = f.readline()
        if line.startswith("#"):
            line = line.replace("\n", "")
            args = line.split()
            if "noplug" in args:
                return False
        return True

    @staticmethod
    def load_plugin(from_file: str) -> tuple:
        """
        Создает модуль из переданного файла-плагина и получает необходимые поля для PluginData.
        :param from_file: путь до файла-плагина.

        :return: плагин, поля плагина.
        """
        spec = importlib.util.spec_from_file_location(f"plugins.{from_file[:-3]}", f"plugins/{from_file}")
        plugin = importlib.util.module_from_spec(spec)
        sys.modules[f"plugins.{from_file[:-3]}"] = plugin
        spec.loader.exec_module(plugin)

        fields = ["NAME", "VERSION", "DESCRIPTION", "CREDITS", "SETTINGS_PAGE", "UUID", "BIND_TO_DELETE"]
        result = {}

        for i in fields:
            try:
                value = getattr(plugin, i)
            except AttributeError:
                import Utils.exceptions
                raise Utils.exceptions.FieldNotExistsError(i, from_file)
            result[i] = value
        return plugin, result

    @staticmethod
    def is_uuid_valid(uuid: str) -> bool:
        """
        Проверяет, валиден ли UUID.

        :param uuid: UUID для проверки.

        :return: True, если UUID валиден, иначе - False.
        """
        try:
            UUID(uuid)
            return True
        except:
            return False

    def load_plugins(self):
        """
        Импортирует все плагины из папки plugins.
        """
        from locales.localizer import Localizer
        localizer = Localizer()
        _ = localizer.translate
        
        if not os.path.exists("plugins"):
            logger.warning(_("crd_no_plugins_folder"))
            return
        plugins = [file for file in os.listdir("plugins") if file.endswith(".py") and file != "__init__.py"]
        if not plugins:
            logger.info(_("crd_no_plugins"))
            return

        sys.path.append("plugins")
        for file in plugins:
            try:
                if not self.is_plugin(file):
                    continue
                plugin, data = self.load_plugin(file)
            except Exception as e:
                logger.error(_("crd_plugin_load_err", file))
                logger.debug("TRACEBACK", exc_info=True)
                continue

            if not self.is_uuid_valid(data["UUID"]):
                logger.error(_("crd_invalid_uuid", file))
                continue

            if data["UUID"] in self.plugins:
                logger.error(_("crd_uuid_already_registered", data['UUID'], data['NAME']))
                continue

            plugin_data = PluginData(data["NAME"], data["VERSION"], data["DESCRIPTION"], data["CREDITS"], data["UUID"],
                                     f"plugins/{file}", plugin, data["SETTINGS_PAGE"], data["BIND_TO_DELETE"],
                                     False if data["UUID"] in self.disabled_plugins else True)

            self.plugins[data["UUID"]] = plugin_data

    def add_handlers_from_plugin(self, plugin, uuid: str | None = None):
        """
        Добавляет хэндлеры из плагина + присваивает каждому хэндлеру UUID плагина.

        :param plugin: модуль (плагин).
        :param uuid: UUID плагина (None для встроенных хэндлеров).
        """
        for name in self.handler_bind_var_names:
            try:
                functions = getattr(plugin, name)
            except AttributeError:
                continue
            for func in functions:
                func.plugin_uuid = uuid
            self.handler_bind_var_names[name].extend(functions)
        from locales.localizer import Localizer
        localizer = Localizer()
        _ = localizer.translate
        logger.info(_("crd_handlers_registered", plugin.__name__))

    def add_handlers(self):
        """
        Регистрирует хэндлеры из всех плагинов.
        """
        for i in self.plugins:
            plugin = self.plugins[i].plugin
            self.add_handlers_from_plugin(plugin, i)

    def toggle_plugin(self, uuid):
        """
        Активирует / деактивирует плагин.
        :param uuid: UUID плагина.
        """
        self.plugins[uuid].enabled = not self.plugins[uuid].enabled
        if self.plugins[uuid].enabled and uuid in self.disabled_plugins:
            self.disabled_plugins.remove(uuid)
        elif not self.plugins[uuid].enabled and uuid not in self.disabled_plugins:
            self.disabled_plugins.append(uuid)
        cardinal_tools.cache_disabled_plugins(self.disabled_plugins)

    def add_telegram_commands(self, uuid: str, commands: list[tuple[str, str, bool]]):
        """
        Добавляет команды в список команд плагина.
        [
            ("команда1", "описание команды", Добавлять ли в меню команд (True / False)),
            ("команда2", "описание команды", Добавлять ли в меню команд (True / False))
        ]

        :param uuid: UUID плагина.
        :param commands: список команд (без "/")
        """
        if uuid not in self.plugins:
            return

        for i in commands:
            self.plugins[uuid].commands[i[0]] = i[1]
            if i[2] and self.telegram:
                self.telegram.add_command_to_menu(i[0], i[1])
