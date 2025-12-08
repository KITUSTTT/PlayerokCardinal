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
    # В PlayerokAPI используется message.user, а не message.author
    if hasattr(message, 'user') and message.user:
        author = message.user.username if hasattr(message.user, 'username') else str(message.user.id)
    else:
        author = "Unknown"
    logger.info(_("log_new_msg", chat_name, chat.id))
    logger.info(f"$MAGENTA└───> $YELLOW{author}: $CYAN{message.text or ''}")

def send_new_message_notification(c: Cardinal, event: NewMessageEvent):
    """Отправляет уведомление о новом сообщении в Telegram"""
    if c.telegram is None:
        return
    
    message = event.message
    chat = event.chat
    
    # Пропускаем сообщения от бота
    if hasattr(message, 'user') and message.user:
        if hasattr(message.user, 'id') and str(message.user.id) == str(c.account.id):
            return
    
    # Получаем имя автора
    if hasattr(message, 'user') and message.user:
        author_username = message.user.username if hasattr(message.user, 'username') else str(message.user.id)
    else:
        author_username = "Unknown"
    
    # Получаем имя чата
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    
    # Формируем текст сообщения
    message_text = message.text if message.text else "[Медиа]"
    if len(message_text) > 100:
        message_text = message_text[:97] + "..."
    
    # Формируем текст уведомления
    notification_text = f"💬 <b>Новое сообщение</b>\n\n"
    notification_text += f"👤 <b>От:</b> {author_username}\n"
    notification_text += f"💬 <b>Чат:</b> {chat_name}\n"
    notification_text += f"📝 <b>Сообщение:</b> {message_text}"
    
    # Создаем клавиатуру с кнопками
    from tg_bot.keyboards import reply
    from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B
    from tg_bot import CBT
    from locales.localizer import Localizer
    
    localizer = Localizer()
    _ = localizer.translate
    
    # Создаем клавиатуру вручную, так как reply ожидает int, а у нас UUID
    keyboard = K()
    keyboard.row(
        B(_("msg_reply2"), None, f"{CBT.SEND_FP_MESSAGE}:{chat.id}:{author_username}"),
        B(_("msg_templates"), None, f"{CBT.TMPLT_LIST_ANS_MODE}:0:{chat.id}:{author_username}:1:1")
    )
    keyboard.row(B(_("msg_more"), None, f"{CBT.EXTEND_CHAT}:{chat.id}:{author_username}"))
    keyboard.row(B(f"🌐 {author_username}", url=f"https://playerok.com/chats/{chat.id}"))
    
    # Отправляем уведомление
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.new_message
    )

def send_response_handler(c: Cardinal, event: NewMessageEvent):
    """Отправляет автоответ на сообщение"""
    if not c.autoresponse_enabled:
        return
    
    message = event.message
    chat = event.chat
    
    if not message.text:
        return
    
    mtext = message.text.strip().lower()
    
    # В PlayerokAPI используется message.user, а не message.author
    if hasattr(message, 'user') and message.user:
        author_username = message.user.username if hasattr(message.user, 'username') else str(message.user.id)
    else:
        author_username = "Unknown"
    if author_username in c.blacklist:
        logger.info(f"Пользователь $YELLOW{author_username}$RESET в черном списке, игнорируем.")
        return
    
    if mtext not in c.AR_CFG:
        return
    
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    logger.info(_("log_new_cmd", mtext, chat_name, chat.id))
    response = c.AR_CFG[mtext]["response"]
    # Форматируем переменные в ответе
    response = cardinal_tools.format_msg_text(response, message)
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
                # Форматируем переменные в ответе автовыдачи
                response = cardinal_tools.format_order_text(response, deal)
                # В PlayerokAPI для ItemDeal используется user, а не buyer
                buyer_name = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else ""
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

def create_deal_keyboard(chat_id: str, username: str, deal_id: str):
    """Создает клавиатуру для уведомлений о сделках"""
    from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B
    from tg_bot import CBT
    from locales.localizer import Localizer
    
    localizer = Localizer()
    _ = localizer.translate
    
    keyboard = K()
    keyboard.row(
        B(_("msg_reply"), None, f"{CBT.SEND_FP_MESSAGE}:{chat_id}:{username}"),
        B(_("msg_templates"), None, f"{CBT.TMPLT_LIST_ANS_MODE}:0:{chat_id}:{username}:0:0")
    )
    keyboard.row(B(f"🌐 {username}", url=f"https://playerok.com/chats/{chat_id}"))
    keyboard.row(B("📋 Сделка", url=f"https://playerok.com/deals/{deal_id}/"))
    return keyboard

def send_new_deal_notification(c: Cardinal, event: NewDealEvent):
    """Отправляет уведомление о новой сделке в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    # Получаем имя покупателя
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    
    # Получаем имя товара
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    
    # Получаем цену
    price = deal.item.price if hasattr(deal, 'item') and hasattr(deal.item, 'price') else 0
    
    notification_text = f"🛒 <b>Новая сделка!</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"💰 <b>Цена:</b> {price / 100 if price else 0:.2f} RUB\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.new_order
    )

def send_item_paid_notification(c: Cardinal, event: ItemPaidEvent):
    """Отправляет уведомление об оплате товара в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    price = deal.item.price if hasattr(deal, 'item') and hasattr(deal.item, 'price') else 0
    
    notification_text = f"💳 <b>Товар оплачен!</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"💰 <b>Цена:</b> {price / 100 if price else 0:.2f} RUB\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.new_order
    )

def send_item_sent_notification(c: Cardinal, event: ItemSentEvent):
    """Отправляет уведомление об отправке товара в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    
    notification_text = f"📤 <b>Товар отправлен!</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.delivery
    )

def send_deal_confirmed_notification(c: Cardinal, event: DealConfirmedEvent):
    """Отправляет уведомление о подтверждении сделки в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    price = deal.item.price if hasattr(deal, 'item') and hasattr(deal.item, 'price') else 0
    
    notification_text = f"✅ <b>Сделка подтверждена!</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"💰 <b>Цена:</b> {price / 100 if price else 0:.2f} RUB\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.order_confirmed
    )

def send_deal_rolled_back_notification(c: Cardinal, event: DealRolledBackEvent):
    """Отправляет уведомление о возврате сделки в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    
    notification_text = f"↩️ <b>Сделка возвращена!</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.other
    )

def send_new_review_notification(c: Cardinal, event: NewReviewEvent):
    """Отправляет уведомление о новом отзыве в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    
    # Получаем отзыв
    review_text = ""
    review_rating = 0
    if hasattr(deal, 'review') and deal.review:
        if hasattr(deal.review, 'text'):
            review_text = deal.review.text
        if hasattr(deal.review, 'rating'):
            review_rating = deal.review.rating
    
    stars = "⭐" * review_rating if review_rating else ""
    
    notification_text = f"⭐ <b>Новый отзыв!</b>\n\n"
    notification_text += f"👤 <b>От:</b> {buyer_username}\n"
    notification_text += f"{stars}\n"
    if review_text:
        if len(review_text) > 200:
            review_text = review_text[:197] + "..."
        notification_text += f"💬 <b>Текст:</b> {review_text}\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.review
    )

def send_deal_has_problem_notification(c: Cardinal, event: DealHasProblemEvent):
    """Отправляет уведомление о проблеме в сделке в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    
    notification_text = f"⚠️ <b>Проблема в сделке!</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.critical
    )

def send_deal_problem_resolved_notification(c: Cardinal, event: DealProblemResolvedEvent):
    """Отправляет уведомление о решении проблемы в сделке в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    
    notification_text = f"✅ <b>Проблема решена!</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.other
    )

def send_deal_status_changed_notification(c: Cardinal, event: DealStatusChangedEvent):
    """Отправляет уведомление об изменении статуса сделки в Telegram"""
    if c.telegram is None:
        return
    
    deal = event.deal
    chat = event.chat
    
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    
    status_name = str(deal.status) if hasattr(deal, 'status') else "Неизвестный"
    
    notification_text = f"🔄 <b>Статус сделки изменен</b>\n\n"
    notification_text += f"👤 <b>Покупатель:</b> {buyer_username}\n"
    notification_text += f"📦 <b>Товар:</b> {item_name}\n"
    notification_text += f"📊 <b>Новый статус:</b> {status_name}\n"
    notification_text += f"🆔 <b>ID сделки:</b> <code>{deal.id}</code>"
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    c.telegram.send_notification(
        text=notification_text,
        keyboard=keyboard,
        notification_type=NotificationTypes.other
    )

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
    
    # Форматируем баланс (баланс уже в рублях, не делим на 100)
    balance_rub = balance.value if balance.value else 0
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
    c.new_message_handlers.append(send_new_message_notification)
    c.new_message_handlers.append(send_response_handler)
    
    # Уведомления о сделках
    c.new_deal_handlers.append(send_new_deal_notification)
    c.new_deal_handlers.append(auto_delivery_handler)
    
    c.item_paid_handlers.append(send_item_paid_notification)
    c.item_paid_handlers.append(auto_delivery_handler)
    
    c.item_sent_handlers.append(send_item_sent_notification)
    c.deal_confirmed_handlers.append(send_deal_confirmed_notification)
    c.deal_rolled_back_handlers.append(send_deal_rolled_back_notification)
    c.new_review_handlers.append(send_new_review_notification)
    c.deal_has_problem_handlers.append(send_deal_has_problem_notification)
    c.deal_problem_resolved_handlers.append(send_deal_problem_resolved_notification)
    c.deal_status_changed_handlers.append(send_deal_status_changed_notification)
    
    logger.info("Обработчики зарегистрированы!")


BIND_TO_POST_INIT = [send_bot_started_notification_handler]
