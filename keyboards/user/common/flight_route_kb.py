import time
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram_calendar import SimpleCalendar

from core import bot, dp
from config import MESSAGE_DELAY
from data.database.database import executeone, fetchone, fetchmany
from data.database.db_api import fetchmany_countries
from keyboards.user.common.common_inline_kb import cancel_button_IK, main_menu_message_IK
from keyboards.user.customer.customer_kb import terminate_order_message_IK
from keyboards.user.order.common_order_kb import show_order_PREVIEW_message_IK
from utils.chat_mgmt import delete_message, get_last_message


async def countries(user_id: int, direction: str, role: str, order_id: int = None, text: str = None):
    """
    by iso_code\n
    callback_data = f"{order_id}_set-{direction}-country_{role}_{country['name_eng']}_{country['iso_code']}"\n
    :param text:
    :param role:
    :param order_id:
    :param user_id:
    :param direction: 'departure' or 'arrival'
    :return:
    """
    if order_id is None:
        order_id = ' '

    _direction_text = '*откуда* Вам нужно отправить посылку' if direction == 'departure' else 'где посылку *будут встречать*'
    direction_emoji = '🛫' if direction == 'departure' else '🛬'
    direction_text = f"{direction_emoji}Выберите страну и город, *{_direction_text}*:"

    IK = types.InlineKeyboardMarkup(row_width=2)
    _countries = await fetchmany_countries()
    if len(_countries) > 0:
        for country in _countries:
            callback_data = f"{order_id}_set-{direction}-country_{role}_{country['name_eng']}_{country['iso_code']}"
            country_text = f"{country['name_rus'] if country['name_rus'] else country['name_eng']} {country['flag']}"
            IK.insert(types.InlineKeyboardButton(country_text, callback_data=callback_data))
        if direction == 'arrival':
            IK.row(types.InlineKeyboardButton('👈 Назад',
                                              callback_data=f"{order_id}_set-departure-country-back_{role}"),
                   types.InlineKeyboardButton('👈 Меню',
                                              callback_data=await cancel_button_IK(order_id,
                                                                                   get_btn_callback_data=True)))
        IK.row(await cancel_button_IK(order_id))
        await bot.send_message(user_id, f"{text if text else direction_text}", parse_mode=types.ParseMode.MARKDOWN,
                               reply_markup=IK)
        return True
    else:
        await bot.send_message(user_id, f"Страна отсутствует в базе данных", reply_markup=IK)
        await main_menu_message_IK(user_id)
        return False


async def cities(user_id: int, direction: str, iso_code: str, role: str, order_id: int = None, text: str = None):
    """
    by iso_code\n
    callback_data = f"{order_id}_set-{direction}-city_{role}_{airport['iata_code']}_{airport['city_eng']}"\n
    :param text:
    :param role:
    :param iso_code:
    :param order_id:
    :param user_id:
    :param direction: 'departure' or 'arrival'
    :return:
    """
    if order_id is None:
        order_id = ' '
    direction_emoji = '🛫' if direction == 'departure' else '🛬'

    country = await fetchone('''SELECT * FROM bot.country WHERE iso_code = $1''', [iso_code])
    airports_table = await fetchmany('''SELECT * FROM bot.airport WHERE iso_code = $1 ORDER BY city_eng''', [iso_code])

    IK = types.InlineKeyboardMarkup(row_width=2)
    if len(airports_table) > 0 and len(country) > 0:
        for airport in airports_table:
            callback_data = f"{order_id}_set-{direction}-city_{role}_{airport['iata_code']}_{airport['city_eng']}"
            airport_text = f"{airport['city_rus'] if airport['city_rus'] else airport['city_eng']}|{airport['iata_code']}"
            IK.insert(types.InlineKeyboardButton(airport_text, callback_data=callback_data))
        IK.row(types.InlineKeyboardButton('👈 Назад',
                                          callback_data=f"{order_id}_set-{direction}-country-back_{role}"),
               types.InlineKeyboardButton('👈 Меню',
                                          callback_data=await cancel_button_IK(order_id, get_btn_callback_data=True)))
        IK.row(await cancel_button_IK(order_id))
        original_text = f"{direction_emoji}{country['flag']}Выберите город, страна *{country['name_rus']}:*"
        await bot.send_message(user_id, f"{text if text else original_text}",
                               parse_mode=types.ParseMode.MARKDOWN,
                               reply_markup=IK)
        return True
    else:
        await bot.send_message(user_id, f"Города для выбранной страны отсутствуют в базе данных", reply_markup=IK)
        return False


async def departure_date_calendar_message_IK(callback_query: types.CallbackQuery, callback_data: dict,
                                             state: FSMContext, role: str):
    data = await dp.current_state(chat=callback_query.from_user.id, user=callback_query.from_user.id).get_data()
    # noinspection PyTypeChecker
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        q = '''UPDATE bot."order" SET departure_date = $2, departure_date_posix = $3 WHERE id = $1'''
        await executeone(q, [data['order_id'], date.strftime("%d/%m/%Y"),
                             time.mktime(datetime.date(date).timetuple())])

        await delete_message(callback_query.from_user.id, data['calendar_msg_ids'], MESSAGE_DELAY)
        await START_departure_country_message_IK(callback_query.from_user.id, role, data['order_id'])
        await state.finish()


async def departure_date_cancel_message_IK(message: types.Message, state: FSMContext):
    data = await dp.current_state(chat=message.from_user.id, user=message.from_user.id).get_data()
    try:
        if message.text == '❌ Отмена':
            await delete_message(message.from_user.id, data['calendar_msg_ids'], MESSAGE_DELAY)
            await terminate_order_message_IK(message.from_user.id, data['order_id'])
            await state.finish()
    except AttributeError:
        pass


async def START_departure_country_message_IK(user_id: int, role: str, order_id: int = None, text: str = None):
    await countries(user_id, 'departure', role, order_id, text)


async def SECOND_departure_city_message_IK(user_id: int, departure_country_iso_code: str, role: str,
                                           order_id: int = None):
    return await cities(user_id, 'departure', departure_country_iso_code, role, order_id)


async def THIRD_arrival_country_message_IK(user_id: int, role: str, order_id: int = None, text: str = None):
    await countries(user_id, 'arrival', role, order_id, text)


async def END_arrival_city_message_IK(user_id: int, arrival_country_iso_code: str, role: str, order_id: int = None,
                                      text: str = None):
    return await cities(user_id, 'arrival', arrival_country_iso_code, role, order_id, text)


async def order_comment_message_IK(message: types.Message, state: FSMContext, role: str):  # TODO ошбика парсинга [[
    await delete_message(message.from_user.id, await get_last_message(message.from_user.id), MESSAGE_DELAY)
    data = await dp.current_state(chat=message.from_user.id, user=message.from_user.id).get_data()
    async with state.proxy():
        if not message.text.startswith('/'):
            q = '''UPDATE bot."order" SET comment = $2 WHERE id = $1'''
            await executeone(q, [data['order_id'], message.text])
            await state.finish()
            await show_order_PREVIEW_message_IK(message.from_user.id, data['order_id'], role)
        elif message.text == '❌ Отмена' or message.text.startswith('/'):
            await terminate_order_message_IK(message.from_user.id, data['order_id'])
            await state.finish()
        else:
            await message.answer('Неправильный формат ввода')
