import asyncio

from aiogram import types

from core import dp, bot
from config import MESSAGE_DELAY, customer_flight_route_comment_ITEM, contractor_flight_route_comment_ITEM
from data.database.database import executeone, fetchone
from data.database.db_api import fetchone_order
from keyboards.user.common.flight_route_kb import SECOND_departure_city_message_IK, THIRD_arrival_country_message_IK, \
    START_departure_country_message_IK, END_arrival_city_message_IK
from states.ContractorStates import ContractorStates
from states.CustomerStates import CustomerStates
from utils.chat_mgmt import save_message, delete_message, get_last_message


def reg_flight_route_handlers():
    dp.register_callback_query_handler(START_set_departure_country,
                                       lambda c: str(c.data).split('_')[1] == "set-departure-country")
    dp.register_callback_query_handler(set_departure_country_BACK,
                                       lambda c: str(c.data).split('_')[1] == "set-departure-country-back")
    dp.register_callback_query_handler(set_departure_city,
                                       lambda c: str(c.data).split('_')[1] == "set-departure-city")
    dp.register_callback_query_handler(set_arrival_country,
                                       lambda c: str(c.data).split('_')[1] == "set-arrival-country")
    dp.register_callback_query_handler(set_arrival_country_BACK,
                                       lambda c: str(c.data).split('_')[1] == "set-arrival-country-back")
    dp.register_callback_query_handler(END_set_arrival_city,
                                       lambda c: str(c.data).split('_')[1] == "set-arrival-city")


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "set-departure-country")
async def START_set_departure_country(callback_query: types.CallbackQuery):
    await delete_message(callback_query.from_user.id, await get_last_message(callback_query.from_user.id),
                         MESSAGE_DELAY)
    role = callback_query.data.split('_')[-3]
    country_name_eng = callback_query.data.split('_')[-2]
    country_iso_code = callback_query.data.split('_')[-1]
    order_id = int(callback_query.data.split('_')[0])
    if await SECOND_departure_city_message_IK(callback_query.from_user.id, country_iso_code, role, order_id):
        q = '''UPDATE bot."order" SET departure_country = $2 WHERE id = $1'''
        await executeone(q, [order_id, country_name_eng])
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "set-departure-city")
async def set_departure_city(callback_query: types.CallbackQuery):
    spl = callback_query.data.split('_')
    role = spl[-3]
    departure_airport_abbr = spl[-2]
    order_id = int(spl[0])
    city = spl[-1]
    q = '''UPDATE bot."order" SET departure_city = $2,  departure_airport_abbr = $3 WHERE id = $1'''
    await executeone(q, [order_id, city, departure_airport_abbr])
    await THIRD_arrival_country_message_IK(callback_query.from_user.id, role, order_id)
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "set-departure-country-back")
async def set_departure_country_BACK(callback_query: types.CallbackQuery):
    spl = callback_query.data.split('_')
    role = spl[-1]
    order_id = int(spl[0])
    await START_departure_country_message_IK(callback_query.from_user.id, role, order_id)
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "set-arrival-country")
async def set_arrival_country(callback_query: types.CallbackQuery):
    role = callback_query.data.split('_')[-3]
    country_name_eng = callback_query.data.split('_')[-2]
    country_iso_code = callback_query.data.split('_')[-1]
    order_id = int(callback_query.data.split('_')[0])
    if await END_arrival_city_message_IK(callback_query.from_user.id, country_iso_code, role, order_id):
        q = '''UPDATE bot."order" SET arrival_country = $2 WHERE id = $1'''
        await executeone(q, [order_id, country_name_eng])
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "set-arrival-arrival_city")
async def END_set_arrival_city(callback_query: types.CallbackQuery):
    spl = callback_query.data.split('_')
    role = callback_query.data.split('_')[-3]
    arrival_airport_abbr = spl[-2]
    arrival_city = spl[-1]
    order_id = int(spl[0])
    q_1 = '''UPDATE bot."order" SET arrival_city = $2, arrival_airport_abbr = $3 WHERE id = $1'''
    await executeone(q_1, [order_id, arrival_city, arrival_airport_abbr])

    current_order = await fetchone_order(order_id)

    departure_name_eng = current_order['departure_country']
    arrival_name_eng = current_order['arrival_country']

    q_dp_country = '''SELECT flag FROM bot.country WHERE name_eng = $1'''
    departure_country = await fetchone(q_dp_country, [departure_name_eng])

    q_ar_country = '''SELECT flag FROM bot.country WHERE name_eng = $1'''
    arrival_country = await fetchone(q_ar_country, [arrival_name_eng])

    address_from = f"{departure_country['flag'] if len(departure_country) > 0 else ''}{current_order.get('departure_country')}," \
                   f" {current_order.get('departure_city')}|{current_order.get('departure_airport_abbr')}"
    address_to = f" - {arrival_country['flag'] if len(arrival_country) > 0 else ''}{current_order.get('arrival_country')}," \
                 f" {current_order.get('arrival_city')}|{current_order.get('arrival_airport_abbr')}"
    flight_route = address_from + address_to

    q_2 = '''UPDATE bot."order" SET flight_route = $2 WHERE id = $1'''
    await executeone(q_2, [order_id, flight_route])

    flight_route_comment_TEXT = \
        f"*✒  Добавьте комментарий к объявлению, чтобы сделать его более заметным!*\n\n" \
        f"👌  Тут можете указать:\n\n" \
        f"{customer_flight_route_comment_ITEM if role == 'customer' else contractor_flight_route_comment_ITEM}"
    msg = await bot.send_message(callback_query.from_user.id, flight_route_comment_TEXT,
                                 parse_mode=types.ParseMode.MARKDOWN)
    await save_message(callback_query.from_user.id, msg.message_id)
    if role == 'customer':
        await CustomerStates.set_order_comment.set()
    elif role == 'contractor':
        await ContractorStates.set_order_comment.set()
    await dp.current_state(chat=callback_query.from_user.id, user=callback_query.from_user.id) \
        .set_data({'order_id': order_id})
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "set-arrival-country-back")
async def set_arrival_country_BACK(callback_query: types.CallbackQuery):
    spl = callback_query.data.split('_')
    role = spl[-1]
    order_id = int(spl[0])
    await THIRD_arrival_country_message_IK(callback_query.from_user.id, role, order_id)
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()
