from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cardinal import Cardinal

from PlayerokAPI.listener.events import *
from Utils import cardinal_tools
from locales.localizer import Localizer
import logging
import time

logger = logging.getLogger("POC.handlers")
localizer = Localizer()
_ = localizer.translate

def log_msg_handler(c: Cardinal, event: NewMessageEvent):
    """Логирует новое сообщение"""
    message = event.message
    chat = event.chat
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    author = message.author.username if hasattr(message.author, 'username') else str(message.author)
    logger.info(_("log_new_msg", chat_name, chat.id))
    logger.info(f"$MAGENTA└───> $YELLOW{author}: $CYAN{message.text or ''}")

def send_response_handler(c: Cardinal, event: NewMessageEvent):
    """Отправляет автоответ на сообщение"""
    if not c.autoresponse_enabled:
        return
    
    message = event.message
    chat = event.chat
    
    if not message.text:
        return
    
    mtext = message.text.strip().lower()
    
    author_username = message.author.username if hasattr(message.author, 'username') else str(message.author)
    if author_username in c.blacklist:
        logger.info(f"Пользователь $YELLOW{author_username}$RESET в черном списке, игнорируем.")
        return
    
    if mtext not in c.AR_CFG:
        return
    
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    logger.info(_("log_new_cmd", mtext, chat_name, chat.id))
    response = c.AR_CFG[mtext]["response"]
    c.send_message(chat.id, response, chat_name)

def auto_delivery_handler(c: Cardinal, event: NewDealEvent | ItemPaidEvent):
    """Обрабатывает автовыдачу для нового заказа"""
    if not c.autodelivery_enabled:
        return
    
    deal = event.deal
    chat = event.chat
    
    logger.info(f"Обработка заказа $YELLOW#{deal.id}$RESET")
    
    # Получаем lot_id из deal
    lot_id = None
    if hasattr(deal, 'item') and deal.item:
        if hasattr(deal.item, 'id'):
            lot_id = str(deal.item.id)
        elif hasattr(deal.item, 'lot_id'):
            lot_id = str(deal.item.lot_id)
    
    if not lot_id:
        logger.warning(f"Не удалось определить lot_id для заказа $YELLOW#{deal.id}$RESET")
        return
    
    for delivery_config in c.AD_CFG:
        if delivery_config.get("lot_id") == lot_id:
            logger.info(f"Найдена конфигурация автовыдачи для лота $YELLOW{lot_id}$RESET")
            
            goods_file = delivery_config.get("goods_file")
            response = delivery_config.get("response", "")
            
            if not goods_file:
                logger.error(f"Не указан файл товаров для лота $YELLOW{lot_id}$RESET")
                continue
            
            try:
                with open(goods_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                if not lines:
                    logger.error(f"Файл $YELLOW{goods_file}$RESET пуст!")
                    continue
                
                product = lines[0].strip()
                
                with open(goods_file, "w", encoding="utf-8") as f:
                    f.writelines(lines[1:])
                
                response = response.replace("$product", product)
                buyer_name = deal.buyer.username if hasattr(deal, 'buyer') and hasattr(deal.buyer, 'username') else ""
                c.send_message(chat.id, response, buyer_name)
                
                logger.info(f"Товар для заказа $YELLOW#{deal.id}$RESET выдан: $CYAN{product}$RESET")
            except Exception as e:
                logger.error(f"Ошибка при автовыдаче: $YELLOW{e}$RESET")
            
            break

def chat_initialized_handler(c: Cardinal, event: ChatInitializedEvent):
    """Обрабатывает инициализацию чата"""
    chat = event.chat
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    logger.info(f"Инициализирован чат $YELLOW{chat_name} (ID: {chat.id})$RESET")

def send_bot_started_notification_handler(c: Cardinal, *args):
    """
    Отправляет уведомление о запуске бота в телеграм.
    """
    if c.telegram is None:
        return
    # Получаем баланс
    balance = c.balance
    if balance is None:
        balance = c.get_balance()
    
    # Получаем активные заказы
    active_sales = 0
    try:
        if hasattr(c.account, 'profile') and c.account.profile and hasattr(c.account.profile, 'stats'):
            if hasattr(c.account.profile.stats, 'deals') and c.account.profile.stats.deals:
                if hasattr(c.account.profile.stats.deals, 'incoming') and c.account.profile.stats.deals.incoming:
                    active_sales = getattr(c.account.profile.stats.deals.incoming, 'total', 0)
    except:
        pass
    
    # Форматируем баланс
    balance_rub = balance.value / 100 if balance.value else 0
    balance_usd = 0.0  # PlayerokAPI не возвращает USD напрямую
    balance_eur = 0.0  # PlayerokAPI не возвращает EUR напрямую
    
    text = _("poc_init", c.VERSION, c.account.username, c.account.id,
             balance_rub, balance_usd, balance_eur, active_sales)
    for i in c.telegram.init_messages:
        try:
            c.telegram.bot.edit_message_text(text, i[0], i[1])
        except:
            continue


def register_handlers(c: Cardinal):
    """Регистрирует все обработчики событий"""
    logger.info("Регистрация обработчиков...")
    
    # Регистрируем обработчики через BIND_TO_*
    if hasattr(c, 'handler_bind_var_names'):
        # Импортируем модули с BIND_TO_*
        import handlers as handlers_module
        for var_name, handler_list in c.handler_bind_var_names.items():
            if hasattr(handlers_module, var_name):
                bind_list = getattr(handlers_module, var_name)
                handler_list.extend(bind_list)
    
    c.chat_initialized_handlers.append(chat_initialized_handler)
    c.new_message_handlers.append(log_msg_handler)
    c.new_message_handlers.append(send_response_handler)
    c.new_order_handlers.append(auto_delivery_handler)
    c.item_paid_handlers.append(auto_delivery_handler)
    
    logger.info("Обработчики зарегистрированы!")


BIND_TO_POST_INIT = [send_bot_started_notification_handler]
