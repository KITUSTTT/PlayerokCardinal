from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cardinal import Cardinal

from PlayerokAPI.listener.events import *
from Utils import cardinal_tools
import logging
import time

logger = logging.getLogger("POC.handlers")

def log_msg_handler(c: Cardinal, event: NewMessageEvent):
    """Логирует новое сообщение"""
    message = event.message
    chat = event.chat
    logger.info(f"Новое сообщение в чате {chat.id} от {message.author.username if hasattr(message.author, 'username') else 'Unknown'}: {message.text}")

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
        logger.info(f"Пользователь {author_username} в черном списке, игнорируем.")
        return
    
    if mtext not in c.AR_CFG:
        return
    
    response = c.AR_CFG[mtext]["response"]
    logger.info(f"Отправка автоответа на команду {mtext}")
    c.send_message(chat.id, response, chat.name if hasattr(chat, 'name') else "")

def auto_delivery_handler(c: Cardinal, event: NewDealEvent | ItemPaidEvent):
    """Обрабатывает автовыдачу для нового заказа"""
    if not c.autodelivery_enabled:
        return
    
    deal = event.deal
    chat = event.chat
    
    logger.info(f"Обработка заказа #{deal.id}")
    
    # Получаем lot_id из deal
    lot_id = None
    if hasattr(deal, 'item') and deal.item:
        if hasattr(deal.item, 'id'):
            lot_id = str(deal.item.id)
        elif hasattr(deal.item, 'lot_id'):
            lot_id = str(deal.item.lot_id)
    
    if not lot_id:
        logger.warning(f"Не удалось определить lot_id для заказа #{deal.id}")
        return
    
    for delivery_config in c.AD_CFG:
        if delivery_config.get("lot_id") == lot_id:
            logger.info(f"Найдена конфигурация автовыдачи для лота {lot_id}")
            
            goods_file = delivery_config.get("goods_file")
            response = delivery_config.get("response", "")
            
            if not goods_file:
                logger.error(f"Не указан файл товаров для лота {lot_id}")
                continue
            
            try:
                with open(goods_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                if not lines:
                    logger.error(f"Файл {goods_file} пуст!")
                    continue
                
                product = lines[0].strip()
                
                with open(goods_file, "w", encoding="utf-8") as f:
                    f.writelines(lines[1:])
                
                response = response.replace("$product", product)
                buyer_name = deal.buyer.username if hasattr(deal, 'buyer') and hasattr(deal.buyer, 'username') else ""
                c.send_message(chat.id, response, buyer_name)
                
                logger.info(f"Товар выдан: {product}")
            except Exception as e:
                logger.error(f"Ошибка при автовыдаче: {e}")
            
            break

def chat_initialized_handler(c: Cardinal, event: ChatInitializedEvent):
    """Обрабатывает инициализацию чата"""
    chat = event.chat
    logger.info(f"Инициализирован чат {chat.id}")

def register_handlers(c: Cardinal):
    """Регистрирует все обработчики событий"""
    logger.info("Регистрация обработчиков...")
    
    c.chat_initialized_handlers.append(chat_initialized_handler)
    c.new_message_handlers.append(log_msg_handler)
    c.new_message_handlers.append(send_response_handler)
    c.new_order_handlers.append(auto_delivery_handler)
    c.item_paid_handlers.append(auto_delivery_handler)
    
    logger.info("Обработчики зарегистрированы!")
