from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cardinal import Cardinal

from Utils import cardinal_tools
import logging
import time

logger = logging.getLogger("POC.handlers")

def log_msg_handler(c: Cardinal, message):
    logger.info(f"Новое сообщение от {message.author}: {message.text}")

def send_response_handler(c: Cardinal, message):
    if not c.autoresponse_enabled:
        return
    
    mtext = message.text.strip().lower()
    
    if message.author in c.blacklist:
        logger.info(f"Пользователь {message.author} в черном списке, игнорируем.")
        return
    
    if mtext not in c.AR_CFG:
        return
    
    response = c.AR_CFG[mtext]["response"]
    logger.info(f"Отправка автоответа на команду {mtext}")
    c.send_message(message.chat_id, response, message.chat_name)

def auto_delivery_handler(c: Cardinal, order):
    if not c.autodelivery_enabled:
        return
    
    logger.info(f"Обработка заказа #{order.id}")
    
    for delivery_config in c.AD_CFG:
        if delivery_config["lot_id"] == str(order.lot_id):
            logger.info(f"Найдена конфигурация автовыдачи для лота {order.lot_id}")
            
            goods_file = delivery_config["goods_file"]
            response = delivery_config["response"]
            
            try:
                with open(goods_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                if not lines:
                    logger.error(f"Файл {goods_file} пуст!")
                    return
                
                product = lines[0].strip()
                
                with open(goods_file, "w", encoding="utf-8") as f:
                    f.writelines(lines[1:])
                
                response = response.replace("$product", product)
                c.send_message(order.chat_id, response, order.buyer_name)
                
                logger.info(f"Товар выдан: {product}")
            except Exception as e:
                logger.error(f"Ошибка при автовыдаче: {e}")
            
            break

def register_handlers(c: Cardinal):
    logger.info("Регистрация обработчиков...")
    c.new_message_handlers.append(log_msg_handler)
    c.new_message_handlers.append(send_response_handler)
    c.new_order_handlers.append(auto_delivery_handler)
    logger.info("Обработчики зарегистрированы!")


