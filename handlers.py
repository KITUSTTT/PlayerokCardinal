from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cardinal import Cardinal

from PlayerokAPI.listener.events import *
from Utils import cardinal_tools
import Utils.exceptions
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
    """Отправляет уведомление о новом сообщении в телеграм."""
    if c.telegram is None:
        return
    
    message = event.message
    chat = event.chat
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    
    # Проверяем черный список
    if hasattr(c, 'bl_msg_notification_enabled') and c.bl_msg_notification_enabled and chat_name in c.blacklist:
        return
    
    # Пропускаем сообщения от бота
    if hasattr(message, 'user') and message.user:
        if hasattr(message.user, 'id') and str(message.user.id) == str(c.account.id):
            return
    
    # Проверяем, не является ли сообщение командой (как в FunPayCardinal)
    if message.text:
        mtext = message.text.strip().lower()
        if mtext in c.AR_CFG:
            # Если это команда, не отправляем уведомление (ответ отправит send_response_handler)
            return
    
    # Получаем имя автора
    if hasattr(message, 'user') and message.user:
        author_username = message.user.username if hasattr(message.user, 'username') else str(message.user.id)
        author_id = str(message.user.id) if hasattr(message.user, 'id') else ""
    else:
        author_username = "Unknown"
        author_id = ""
    
    # Формируем текст уведомления в стиле FunPayCardinal
    text = ""
    # Определяем автора сообщения
    if author_id == str(c.account.id):
        author = f"<i><b>🫵 {_('you')}:</b></i> "
    elif author_username in c.blacklist:
        author = f"<i><b>🚷 {author_username}: </b></i>"
    else:
        author = f"<i><b>👤 {author_username}: </b></i>"
    
    # Формируем текст сообщения
    from tg_bot import utils
    msg_text = f"<code>{utils.escape(message.text)}</code>" if message.text else \
        f"<a href=\"{message.file.url if hasattr(message, 'file') and message.file and hasattr(message.file, 'url') else '#'}\">" \
        f"{_('photo')}</a>" if hasattr(message, 'file') and message.file else "[Медиа]"
    
    text = f"{author}{msg_text}\n\n"
    
    # Создаем клавиатуру
    from tg_bot import keyboards
    from tg_bot.utils import NotificationTypes
    kb = keyboards.reply(chat.id, chat_name, extend=True)
    
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(text, kb, NotificationTypes.new_message),
           daemon=True).start()

def send_response_handler(c: Cardinal, event: NewMessageEvent):
    """Проверяет, является ли сообщение командой, и если да, отправляет ответ на данную команду."""
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
    
    if hasattr(c, 'bl_response_enabled') and c.bl_response_enabled and author_username in c.blacklist:
        logger.info(f"Пользователь $YELLOW{author_username}$RESET в черном списке, игнорируем.")
        return
    
    if mtext not in c.AR_CFG:
        return
    
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    logger.info(_("log_new_cmd", mtext, chat_name, chat.id))
    
    # Отправляем ответ на команду
    command_config = c.AR_CFG[mtext]
    response = command_config.get("response", "")
    if response:
        # Форматируем переменные в ответе
        response = cardinal_tools.format_msg_text(response, message)
        from threading import Thread
        Thread(target=c.send_message, args=(chat.id, response, chat_name), daemon=True).start()

def send_command_notification_handler(c: Cardinal, event: NewMessageEvent):
    """Отправляет уведомление о введенной команде в телеграм."""
    if not c.telegram:
        return
    
    message = event.message
    chat = event.chat
    chat_name = chat.name if hasattr(chat, 'name') else str(chat.id)
    
    # В PlayerokAPI используется message.user, а не message.author
    if hasattr(message, 'user') and message.user:
        author_username = message.user.username if hasattr(message.user, 'username') else str(message.user.id)
    else:
        author_username = "Unknown"
    
    # Проверяем черный список
    if hasattr(c, 'bl_cmd_notification_enabled') and c.bl_cmd_notification_enabled and author_username in c.blacklist:
        return
    
    command = message.text.strip().lower() if message.text else ""
    if command not in c.AR_CFG:
        return
    
    # Проверяем, включены ли уведомления для команды
    command_config = c.AR_CFG[command]
    if not command_config.get("telegramNotification", "0") == "1":
        return
    
    # Формируем текст уведомления в стиле FunPayCardinal
    from tg_bot import utils, keyboards
    from tg_bot.utils import NotificationTypes
    from threading import Thread
    
    if not command_config.get("notificationText"):
        text = f"🧑‍💻 Пользователь <b><i>{author_username}</i></b> ввел команду <code>{utils.escape(command)}</code>."
    else:
        text = cardinal_tools.format_msg_text(command_config["notificationText"], message)
    
    Thread(target=c.telegram.send_notification, args=(text, keyboards.reply(chat.id, chat_name),
                                                      NotificationTypes.command), daemon=True).start()

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
    
    # Ищем конфигурацию автовыдачи для этого лота
    delivery_config = None
    for config in c.AD_CFG:
        if config.get("lot_id") == lot_id:
            delivery_config = config
            break
    
    if not delivery_config:
        logger.debug(f"Конфигурация автовыдачи для лота $YELLOW{lot_id}$RESET не найдена")
        return
    
    logger.info(f"Найдена конфигурация автовыдачи для лота $YELLOW{lot_id}$RESET")
    
    goods_file = delivery_config.get("goods_file")
    response = delivery_config.get("response", "")
    
    if not goods_file:
        logger.error(f"Не указан файл товаров для лота $YELLOW{lot_id}$RESET")
        return
    
    # Получаем количество товаров для выдачи
    amount = 1
    # В PlayerokAPI нет поля amount в ItemDeal, используем 1
    
    # Получаем товары из файла
    try:
        result = cardinal_tools.get_products(goods_file, amount)
        if result is None:
            logger.error(f"Файл $YELLOW{goods_file}$RESET пуст или произошла ошибка при чтении!")
            return
        products, goods_left = result
    except Utils.exceptions.NoProductsError:
        logger.error(f"В файле $YELLOW{goods_file}$RESET нет товаров!")
        return
    except Utils.exceptions.NotEnoughProductsError as e:
        logger.error(f"В файле $YELLOW{goods_file}$RESET недостаточно товаров: {e}")
        return
    except Exception as e:
        logger.error(f"Произошла ошибка при получении товаров для заказа $YELLOW#{deal.id}$RESET: $YELLOW{e}$RESET")
        logger.debug("TRACEBACK", exc_info=True)
        return
    
    # Форматируем текст ответа
    delivery_text = cardinal_tools.format_order_text(response, deal)
    # Заменяем $product на товары
    delivery_text = delivery_text.replace("$product", "\n".join(products).replace("\\n", "\n"))
    
    # Отправляем сообщение с товаром
    buyer_name = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    result = c.send_message(chat.id, delivery_text, buyer_name)
    
    if not result:
        logger.error(f"Не удалось отправить товар для ордера $YELLOW#{deal.id}$RESET.")
        # Возвращаем товары обратно в файл
        if products:
            cardinal_tools.add_products(goods_file, products, at_zero_position=True)
        # Отправляем уведомление об ошибке
        if c.telegram:
            from tg_bot.utils import NotificationTypes
            from threading import Thread
            error_text = f"❌ <code>Не удалось отправить товар для ордера {deal.id}.</code>"
            Thread(target=c.telegram.send_notification, args=(error_text, None, NotificationTypes.delivery),
                   daemon=True).start()
    else:
        logger.info(f"Товар для заказа $YELLOW#{deal.id}$RESET выдан: $CYAN{', '.join(products)}$RESET")
        # Отправляем уведомление об успешной выдаче
        if c.telegram:
            from tg_bot import utils
            from tg_bot.utils import NotificationTypes
            from threading import Thread
            amount = "<b>∞</b>" if goods_left == -1 else f"<code>{goods_left}</code>"
            text = f"""✅ Успешно выдал товар для ордера <code>{deal.id}</code>.\n
🛒 <b><i>Товар:</i></b>
<code>{utils.escape(delivery_text)}</code>\n
📋 <b><i>Осталось товаров: </i></b>{amount}"""
            Thread(target=c.telegram.send_notification, args=(text, None, NotificationTypes.delivery),
                   daemon=True).start()

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
    """Отправляет уведомления о новой сделке в телеграм."""
    if not c.telegram:
        return
    
    deal = event.deal
    chat = event.chat
    
    # Получаем имя покупателя
    buyer_username = deal.user.username if hasattr(deal, 'user') and hasattr(deal.user, 'username') else str(deal.user.id) if hasattr(deal, 'user') and deal.user else "Unknown"
    
    # Проверяем черный список
    if buyer_username in c.blacklist and hasattr(c.MAIN_CFG, 'get') and isinstance(c.MAIN_CFG.get("BlockList"), dict) and c.MAIN_CFG.get("BlockList", {}).get("blockNewOrderNotification") == "1":
        return
    
    # Получаем имя товара и категорию
    item_name = deal.item.name if hasattr(deal, 'item') and hasattr(deal.item, 'name') else "Неизвестный товар"
    subcategory_name = ""
    if hasattr(deal, 'item') and deal.item and hasattr(deal.item, 'category') and deal.item.category:
        subcategory_name = deal.item.category.name if hasattr(deal.item.category, 'name') else ""
    
    # Получаем цену (в копейках, делим на 100)
    price = deal.item.price if hasattr(deal, 'item') and hasattr(deal.item, 'price') else 0
    price_rub = price / 100 if price else 0
    
    # Определяем информацию о доставке
    delivery_config = None
    lot_id = str(deal.item.id) if hasattr(deal, 'item') and deal.item and hasattr(deal.item, 'id') else None
    if lot_id:
        for config in c.AD_CFG:
            if config.get("lot_id") == lot_id:
                delivery_config = config
                break
    
    if not delivery_config:
        delivery_info = _("ntfc_new_order_not_in_cfg")
    else:
        if not c.autodelivery_enabled:
            delivery_info = _("ntfc_new_order_ad_disabled")
        else:
            delivery_info = _("ntfc_new_order_will_be_delivered")
    
    # Формируем текст уведомления в стиле FunPayCardinal
    from tg_bot import utils
    description = f"{utils.escape(item_name)}"
    if subcategory_name:
        description += f", {utils.escape(subcategory_name)}"
    
    text = _("ntfc_new_order", description, buyer_username, f"{price_rub:.2f} RUB", deal.id, delivery_info)
    
    keyboard = create_deal_keyboard(str(chat.id), buyer_username, deal.id)
    
    from tg_bot.utils import NotificationTypes
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(text, keyboard, NotificationTypes.new_order),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.new_order),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.delivery),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.order_confirmed),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.other),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.review),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.critical),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.other),
           daemon=True).start()

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
    from threading import Thread
    Thread(target=c.telegram.send_notification, args=(notification_text, keyboard, NotificationTypes.other),
           daemon=True).start()

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
    c.new_message_handlers.append(send_command_notification_handler)
    
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
