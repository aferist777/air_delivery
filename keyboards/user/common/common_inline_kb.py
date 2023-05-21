import asyncio
import typing

from aiogram import types
from aiogram.utils.exceptions import BadRequest

from config import privacy_policy_LINK, MESSAGE_DELAY, about_me_LINK, important_info_BTN_TEXT, \
    donation_service_LINK, CONTRACTOR_ACTIVE_ORDERS_LIMIT, CUSTOMER_ACTIVE_ORDERS_LIMIT, \
    group_chat_LINK
from core import bot, dp, logger
from data.database.database import fetchone
from data.database.db_api import check_user_active_orders, fetchone_user
from handlers.user.common.who_is import is_in_database
from keyboards.user.common.common_reply_kb import RK_verify_phone
from states.OrderStates import OrderStates
from states.UserStates import UserStates
from utils.chat_mgmt import save_message, delete_message, get_last_message


async def base_bot_navigation(user_id: int):
    data = await is_in_database(user_id, True, True)
    if data['checkin_user_table'] and (data['checkin_contractor_table'] or data['checkin_customer_table']):
        await main_menu_message_IK(user_id)
    elif not data['checkin_user_table']:
        await registration_menu_message_IK(user_id)
    else:
        _agree_with_rules = await fetchone('''SELECT agree_with_rules FROM bot.user WHERE user_id = $1''', [user_id])
        if len(_agree_with_rules) > 0:
            await main_menu_message_IK(user_id)
        else:
            await privacy_policy_message_IK(user_id)


async def navigation_menu(user_id: int, cb: str = None, back_to: str = None,
                          messages_id: str = None, delete_yourself: bool = True,
                          message_del_delay: int | float = MESSAGE_DELAY,
                          func: typing.Any = None,
                          *args: typing.Any):
    """
    callback_data=f"{user_id}_back-to-{back_to}_{messages_id if messages_id else ''}"
    callback_data=f"{user_id}_back-to-menu_{messages_id if messages_id else ''}"
    set func or cb
    :param delete_yourself:
    :param message_del_delay:
    :param func: run func
    :param user_id:
    :param cb: custom callback_data
    :param back_to: 'menu' or 'account' or None
    :param messages_id:
    :return:
    """
    if delete_yourself:
        await delete_message(user_id, await get_last_message(user_id), message_del_delay)
    IK_back = types.InlineKeyboardMarkup()
    if back_to:
        back_cb = f"{user_id}_back-to-{back_to}_{messages_id if messages_id else ''}"
        IK_back.insert(types.InlineKeyboardButton('👈 Назад', callback_data=back_cb))
    if cb:
        cb_data = f"{cb}_{messages_id if messages_id else ''}"
        IK_back.insert(types.InlineKeyboardButton('👈 Назад', callback_data=cb_data))
    if func and args:
        func(*args)
    elif func:
        func()
    IK_back.insert(types.InlineKeyboardButton('👈️ В меню',
                                              callback_data=f"{user_id}_back-to-menu_{messages_id if messages_id else ''}"))
    message = await bot.send_message(user_id, 'Навигация', parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK_back)
    if delete_yourself:
        await save_message(user_id, message.message_id)


async def registration_menu_message_IK(user_id: int):
    """
    callback_data=f'{message.from_user.id}_main_menu'
    """
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    text = 'Чтобы начать пользоваться сервисом, Вам нужно пройти регистрацию.'
    IK = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton('Пройти регистрацию', callback_data=f"{user_id}_main_menu"))
    message = await bot.send_message(user_id, text, reply_markup=IK)
    await save_message(user_id, message.message_id)


async def privacy_policy_message_IK(user_id: int):
    """
    callback_data=f'{message.from_user.id}_agree-with-rules_True'
    """
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    IK = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton('👍 Прочитал, согласен!', callback_data=f"{user_id}_agree-with-rules_True"),
        types.InlineKeyboardButton('😔 Не согласен!', callback_data=f"{user_id}_agree-with-rules_False"))
    text = f"Согласие на обработку персональных данных: {privacy_policy_LINK}"
    message = await bot.send_message(user_id, text, parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK,
                                     disable_web_page_preview=True)
    await save_message(user_id, message.message_id)


async def phone_verification_message_IK(user_id: int, role: str):
    try:
        user = await fetchone_user(user_id)
        if len(user) > 0 and not user['phone']:
            await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
            text = """⁉️ Чтобы создать объявление, Вам необходимо подтвердить номер мобильного телефона. 

    😙 Не переживайте, это необходимо для того, чтобы с Вами могли связаться по Вашему объявлению.

    😑Если Вы в чем-то не уверены и хотите еще немного осмотреться и почитать подробнее о сервисе, то мы  Вас не торопим. Как будете готовы - возвращайтесь 😉
    
    Если нет, кнопки «Подтвердить», то нажмите слева от микрофона кнопку с четырьмя точками ↘"""
            message = await bot.send_message(user_id, text, reply_markup=RK_verify_phone(),
                                             parse_mode=types.ParseMode.MARKDOWN)
            await save_message(user_id, message.message_id)
            await UserStates.set_phone.set()
            if role == 'contractor':
                await dp.current_state(chat=user_id, user=user_id).set_data({'role': 'contractor'})
            elif role == 'customer':
                await dp.current_state(chat=user_id, user=user_id).set_data({'role': 'customer'})
        else:
            return True
    except KeyError:
        logger.error(f"phone_verification_message_IK: user_id: {user_id}: user does not exist in 'user' database")
        await base_bot_navigation(user_id)


async def main_menu_message_IK(user_id: int):
    """
    callback_data=f"{user_id}_start-work"
    callback_data=f"{user_id}_ad-search"
    callback_data=f"{user_id}_my-account"
    """
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    text = """Вы находитесь в главном меню
    
*🌐 Начать работу* - Здесь Вы можете разместить Ваше объявление. Если Вы путешествуете, а так же если ищете попутчика для отправления;

*🔎 Поиск объявлений* - Здесь можно найти попутчика или доступные посылки;

*👤 Мой аккаунт* - Здесь будет Ваша личная информация;

*🔵 ВАЖНО* - Инструкции и правила пользования сервисом."""
    num_users = await fetchone('''SELECT count(*) FROM bot."user" WHERE phone is not null''')
    num_travels = await fetchone('''SELECT count(*) FROM bot."order" WHERE role = 'traveler' AND state != $1''',
                                 [OrderStates.order_terminated.state])
    num_senders = await fetchone('''SELECT count(*) FROM bot."order" WHERE role = 'sender' AND state != $1''',
                                 [OrderStates.order_terminated.state])

    stat_vetbose = f"""
    
_Кол-во: пользователей: {num_users['count']} чел.
Кол-во путешествий: {num_travels['count']}
Кол-во посылок: {num_senders['count']}_"""
    text += stat_vetbose

    IK = types.InlineKeyboardMarkup(row_width=2) \
        .add(types.InlineKeyboardButton('🌐 Начать работу', callback_data=f"{user_id}_start-work"),
             types.InlineKeyboardButton('🔎 Поиск объявлений', callback_data=f"{user_id}_ad-search"),
             types.InlineKeyboardButton('👤 Мой аккаунт', callback_data=f"{user_id}_my-account"),
             types.InlineKeyboardButton('🔵 ВАЖНО', callback_data=f"{user_id}_important-info"))
    message = await bot.send_message(user_id, text, reply_markup=IK, parse_mode=types.ParseMode.MARKDOWN)
    await save_message(user_id, message.message_id)
    return message


async def start_work_menu_message_IK(user_id: int):
    """
    callback_data=f"{user_id}_taking-flight"
    callback_data=f"{user_id}_find-companion"
    callback_data=f"{user_id}_back-to-menu"
    """
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    text = """✏ Здесь Вы сможете создать своё объявление.

**👀 - Если Вы хотите найти попутчика, чтобы передать письмо или посылку, то Вам сюда;

✈ -** Если Вы купили билет и хотите предложить свое свободное место в багаже, то Вам сюда;

👈 - Назад. В меню. 😉"""
    IK = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton('👀 Разместить объявление о посылке', callback_data=f"{user_id}_find-companion"),
        types.InlineKeyboardButton('✈ Разместить объявление о путешествии', callback_data=f"{user_id}_taking-flight"),
        types.InlineKeyboardButton('👈 Назад', callback_data=f"{user_id}_back-to-menu"))
    message = await bot.send_message(user_id, text, reply_markup=IK, parse_mode=types.ParseMode.MARKDOWN)
    await save_message(user_id, message.message_id)


async def ad_search_menu_message_IK(user_id: int):
    """
    callback_data=f"{user_id}_get-nearby-customers"
    callback_data=f"{user_id}_get-nearby-contractors"
    callback_data=f"{user_id}_back-to-menu"
    """
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    text = "🔎** Здесь Вы сможете найти ближайших попутчиков, а так же выбрать посылки, которые хотите взять.\n" \
           "\n*Просматривать контакты ближайших путешественников/посылок могут только пользователи, оставившие объявление.*"
    traveler_btn_text = "\n\n[🗣 Путешественники] - Список ближайших попутчиков совпадающих с маршрутом отправления в вашем заказе"
    sender_btn_text = "\n\n[👀 Посылки] - Список посылок совпадающих с маршрутом перелета в вашем заказе"
    text += (sender_btn_text + traveler_btn_text)

    IK = types.InlineKeyboardMarkup(row_width=2)
    res = await check_user_active_orders(user_id)
    if res['customer_has_orders']:
        IK.insert(types.InlineKeyboardButton('👀 Посылки',
                                             callback_data=f"{user_id}_get-nearby-customers_customer-has-orders"))
        IK.insert(types.InlineKeyboardButton('🗣 Путешественники',
                                             callback_data=f"{user_id}_get-nearby-contractors_customer-has-orders"))
    elif res['contractor_has_orders']:
        IK.insert(types.InlineKeyboardButton('👀 Посылки',
                                             callback_data=f"{user_id}_get-nearby-customers_contractor-has-orders_"))
        IK.insert(types.InlineKeyboardButton('🗣 Путешественники',
                                             callback_data=f"{user_id}_get-nearby-contractors_contractor-has-orders_"))
    parcel = types.InlineKeyboardButton('✒ Разместить объявление о посылке',
                                        callback_data=f"{user_id}_find-companion")
    travel = types.InlineKeyboardButton('✒ Разместить объявление о путешествии',
                                        callback_data=f"{user_id}_taking-flight")

    if res['customer_has_orders'] and res['contractor_has_orders']:
        IK.row(parcel)
        IK.add(travel)
    elif res['customer_has_orders']:
        IK.add(travel)
    elif res['contractor_has_orders']:
        IK.add(parcel)
    else:
        IK.row(parcel)
        IK.add(travel)
    IK.row(types.InlineKeyboardButton('👈 Назад', callback_data=f"{user_id}_back-to-menu"))
    message = await bot.send_message(user_id, text, reply_markup=IK, parse_mode=types.ParseMode.MARKDOWN)
    await save_message(user_id, message.message_id)


async def my_account_message_IK(user_id: int):
    """
    callback_data=f"{user_id}_contractor-account"
    callback_data=f"{user_id}_customer-account"
    callback_data=f"{user_id}_back-to-menu"
    """
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    _data = await is_in_database(user_id, False, False)
    if _data['checkin_user_table']:
        user = await fetchone_user(user_id)
        curr_traveler_bio = f'\n{user["traveler_bio"] if user["traveler_bio"] else "..."}'
        curr_sender_bio = f'\n{user["sender_bio"] if user["sender_bio"] else "..."}'
        account_text = f"""😇 Это Ваш аккаунт. Здесь Вы можете управлять своими объявлениями (завершать активные и удалять ненужные объявления). 
        
👤 *Имя*: {user['first_name']} {user['last_name']}
        
✍ *О себе (путешествую)*:
/set\_traveler\_bio
{curr_traveler_bio}
        
✍ *О себе (отправляю)*:
/set\_sender\_bio
{curr_sender_bio}

❓Как правильно заполнить информацию *“О себе” и для чего нужна* {about_me_LINK}"""

        traveler_account_text = "\n\n✈ *Мои путешествия* - Здесь Вы можете смотреть историю Ваших путешествий."
        sender_account_text = "\n\n📦 *Мои Отправления* - Здесь Вы можете смотреть историю Ваших отправлений."
        info_text = " *(Кнопка станет доступна после того как Вы разместите объявление)*"
        IK = types.InlineKeyboardMarkup(row_width=2)
        contractor_has_active_orders = await get_number_active_orders(user_id, 'contractor', as_traveler=True)
        customer_has_active_orders = await get_number_active_orders(user_id, 'customer')

        if contractor_has_active_orders and customer_has_active_orders:
            IK.add(types.InlineKeyboardButton('✈ Мои путешествия', callback_data=f"{user_id}_contractor-account"),
                   types.InlineKeyboardButton('📦 Мои Отправления', callback_data=f"{user_id}_customer-account"))
            account_text += traveler_account_text + sender_account_text
        elif contractor_has_active_orders:
            IK.add(types.InlineKeyboardButton('✈ Мои путешествия', callback_data=f"{user_id}_contractor-account"))
            account_text += traveler_account_text
        elif customer_has_active_orders:
            IK.add(types.InlineKeyboardButton('📦 Мои Отправления', callback_data=f"{user_id}_customer-account"))
            account_text += sender_account_text
        else:
            account_text += traveler_account_text + info_text + sender_account_text + info_text
        try:
            file_id = user['photo']
            _file = await bot.get_file(file_id)
            file = types.InputFile(await bot.download_file(_file.file_path))
        except KeyError:
            file = None
        except TypeError:
            file = None
        except BadRequest:
            file = None
        if file:
            IK.row(types.InlineKeyboardButton('👈 Назад',
                                              callback_data=f"{user_id}_back-to-menu"))
            message = await bot.send_photo(user_id, file, account_text,
                                           parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK)
            await save_message(user_id, message.message_id)
        else:
            IK.row(types.InlineKeyboardButton('👈 Назад',
                                              callback_data=f"{user_id}_back-to-menu"))
            message = await bot.send_message(user_id, account_text, parse_mode=types.ParseMode.MARKDOWN,
                                             reply_markup=IK,
                                             disable_web_page_preview=True)
            await save_message(user_id, message.message_id)
    elif not _data['checkin_user_table']:
        await registration_menu_message_IK(user_id)


async def important_info_message_IK(user_id: int):
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    IK = types.InlineKeyboardMarkup(row_width=1)
    IK.row(types.InlineKeyboardButton('🥂 Чат', callback_data=f"{user_id}_' '", url=group_chat_LINK),
           types.InlineKeyboardButton('👈 Назад', callback_data=f"{user_id}_back-to-menu"))
    IK.row(types.InlineKeyboardButton('👏 Поддержать', callback_data=f"{user_id}_' '", url=donation_service_LINK))
    message = await bot.send_message(user_id, important_info_BTN_TEXT, reply_markup=IK,
                                     parse_mode=types.ParseMode.MARKDOWN, disable_web_page_preview=True)
    await save_message(user_id, message.message_id)
    return message


async def cancel_button_IK(order_id: int, get_btn_callback_data=False):
    """
    callback_data=f"{order_id}_cancel-flight-route"
    """
    cb = f"{order_id}_cancel-flight-route"
    if not get_btn_callback_data:
        return types.InlineKeyboardButton('❌ Отмена', callback_data=cb)
    else:
        return cb


async def get_number_active_orders(user_id: int, role: str, as_traveler=False):
    text = "Вы не можете создавать больше " if not as_traveler else 'Вы не можете доставлять больше '
    delay = 1
    values = [user_id, OrderStates.order_accepted.state, OrderStates.order_in_work.state]
    if role == 'contractor':
        if as_traveler:
            contractor_orders = await fetchone('''SELECT count(*) FROM bot."order"
             WHERE contractor_id = $1 AND role = 'traveler' AND (state = $2 or state = $3)''', values)
        else:
            contractor_orders = await fetchone('''SELECT count(*) FROM bot."order"
                         WHERE customer_id = $1 AND role = 'traveler' AND (state = $2 or state = $3)''', values)
        if contractor_orders['count'] < CONTRACTOR_ACTIVE_ORDERS_LIMIT and not as_traveler:
            return True
        elif contractor_orders['count'] < CUSTOMER_ACTIVE_ORDERS_LIMIT and as_traveler:
            return True
        else:
            last_num = str(CONTRACTOR_ACTIVE_ORDERS_LIMIT).split()[-1]
            _text = text + f'{CONTRACTOR_ACTIVE_ORDERS_LIMIT} объявлен' + ('ий' if last_num != '1' else 'ия') + "❗"
            traveler_text = text + f'{CONTRACTOR_ACTIVE_ORDERS_LIMIT} посыл' + ('ок' if last_num != '1' else 'ки') + "❗"
            message = await bot.send_message(user_id, _text if not as_traveler else traveler_text)
            await asyncio.sleep(MESSAGE_DELAY + delay)
            await delete_message(user_id, str(message.message_id))
            return False
    elif role == 'customer':
        customer_orders = await fetchone('''SELECT count(*) FROM bot."order"
                         WHERE customer_id = $1 AND role = 'sender' AND (state = $2 or state = $3)''', values)
        if customer_orders['count'] < CUSTOMER_ACTIVE_ORDERS_LIMIT and not as_traveler:
            return True
        else:
            last_num = str(CUSTOMER_ACTIVE_ORDERS_LIMIT).split()[-1]
            _text = text + f'{CUSTOMER_ACTIVE_ORDERS_LIMIT} объявлен' + ('ий' if last_num != '1' else 'ия') + "❗"
            message = await bot.send_message(user_id, _text)
            await asyncio.sleep(MESSAGE_DELAY + delay)
            await delete_message(user_id, str(message.message_id))
            return False

