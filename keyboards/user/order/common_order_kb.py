import asyncio
import typing
from collections import defaultdict

from aiogram import types

from config import MESSAGE_DELAY, safety_regulations_LINK, group_chat_LINK_MD, \
    DEBUG_MODE, NUMBER_OF_MATCHING_ADS
from core import bot, dp
from data.database.database import fetchone, executeone, fetchmany
from data.database.db_api import fetchone_order, fetchone_user
from keyboards.user.common.common_inline_kb import navigation_menu, main_menu_message_IK, ad_search_menu_message_IK
from keyboards.user.customer.customer_kb import terminate_order_message_IK
from states.OrderStates import OrderStates
from states.PagionationStates import PaginationStates
from utils.chat_mgmt import save_message, get_last_message, delete_message
from utils.pagination import answer_with_pagination


async def show_order_PREVIEW_message_IK(user_id: int, order_id: int, role: str):
    """
    :param role:
    :param order_id:
    :param user_id:
    :return:
    """
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    user = await fetchone_user(user_id)
    order = await fetchone_order(order_id)
    dp_data = f"\n📅 Дата: {order['departure_date']}\n" if order['role'] == 'contractor' else ""
    text = f"""*Предпросмотр объявления:*

👤 *Ваше имя*: {user['first_name']} {user['last_name']}{dp_data}
🛫 *Маршрут*: {order['departure_city']} - {order['arrival_city']} 
✒ *Комментарий*: {order['comment']}

❗ *Друзья, чтобы пользование сервисом приносило Вам только пользу, обязательно прочитайте* {safety_regulations_LINK}. 

Если всё указано верно и Вы прочитали правила, то нажмите
кнопку _“✔ Опубликовать"_.

Чтобы удалить Вашу заявку сейчас нажмите
кнопку _“❌ Удалить“_."""
    IK = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton('✔ Опубликовать', callback_data=f"{order['id']}_publication-order-yes_{role}"),
        types.InlineKeyboardButton('❌ Удалить', callback_data=f"{order['id']}_create-order-no_{role}"))
    message = await bot.send_message(user_id, text, parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK,
                                     disable_web_page_preview=True)
    await save_message(user_id, message.message_id)


async def get_matching_orders(user_id: int, state: str, inner_role: str, order_by: str,
                              limit: int = NUMBER_OF_MATCHING_ADS):
    opposite_role = 'sender' if inner_role == 'traveler' else 'traveler'
    res = defaultdict()
    values = [user_id, state, inner_role, order_by]
    my_orders = await fetchmany(
        '''SELECT * FROM bot."order" WHERE customer_id = $1 AND state = $2  AND role = $3 ORDER BY $4''', values)
    if len(my_orders) > 0:
        for order in my_orders:
            res[order['id']] = order
    if state != OrderStates.order_in_work.state:
        if len(res) > 0:
            for matching_order in my_orders:
                fm_values = [user_id, matching_order['flight_route'], state, opposite_role, order_by, limit]
                full_match = await fetchmany(
                    '''SELECT * FROM bot."order" WHERE customer_id != $1 AND flight_route = $2  AND state = $3 AND role = $4 ORDER BY $5 LIMIT $6''',
                    fm_values)
                if len(full_match) > 0:
                    for fm in full_match:
                        res[fm['id']] = fm
                else:
                    cm_values = [user_id, matching_order['departure_country'], matching_order['arrival_country'],
                                 opposite_role, state, order_by, limit]
                    country_match = await fetchmany(
                        '''SELECT * FROM bot."order" WHERE customer_id != $1 AND departure_country = $2  AND arrival_country = $3 AND role = $4 AND state = $5 ORDER BY $6 LIMIT $7''',
                        cm_values)
                    if len(country_match) > 0:
                        for cm in country_match:
                            res[cm['id']] = cm
    return res.items()


async def show_orders_BY_STATE_message_IK(user_id: int, role: str, by_state: str, back_callback: str):
    """
    :param back_callback:
    :param by_state:
    :param role: contractor or customer
    :param user_id:
    :return:
    """
    match_list = []
    prepared_messages = []
    if role == 'customer':
        matching_orders = await get_matching_orders(user_id, by_state, 'sender', order_by='departure_date_posix')
        if matching_orders:
            match_list.append(matching_orders)
        if by_state == OrderStates.order_in_work.state:
            my_parcels = await fetchone(
                '''SELECT * FROM bot."order" WHERE customer_id = $1 AND role = 'sender' AND state = $2 ORDER BY create_time''',
                [user_id, by_state])
            for parcel in my_parcels:
                match_list.append(await fetchone(
                    '''SELECT * FROM bot."order" WHERE flight_route = $1 AND role = 'sender' AND state = $2 ORDER BY create_time''',
                    [parcel['flight_route'], by_state]))
    elif role == 'contractor':
        matching_orders = await get_matching_orders(user_id, by_state, 'traveler', order_by='create_time')
        if matching_orders:
            match_list.append(matching_orders)
        if by_state == OrderStates.order_in_work.state:
            my_parcels = await fetchone(
                '''SELECT * FROM bot."order" WHERE contractor_id = $1 AND role = 'sender' AND state = $2 ORDER BY create_time''',
                [user_id, by_state])
            for parcel in my_parcels:
                country_match = await fetchone(
                    '''SELECT * FROM bot."order" WHERE customer_id = $1 AND role = 'sender' AND state = $2 AND flight_route = $3 ORDER BY customer_id''',
                    [parcel['customer_id'], parcel['flight_route'], by_state])
                if len(country_match) > 0:
                    match_list.append(country_match)

    if len(match_list) > 0:
        contact_text = "\n\nНажмите '🔼 Связаться', чтобы написать пользователю."
        for key, order in dict(match_list[0]).items():
            user = await fetchone_user(order['customer_id'])
            order_type = 'Отправление\n' if order['role'] == 'sender' else 'Путешествие\n'
            header_text = 'Ваше объявление.\n' if order['customer_id'] == user_id else ''
            curr_traveler_is_executor_text = 'Вы доставляете этот заказ\n' \
                if order['contractor_id'] == user_id and order['state'] == OrderStates.order_in_work.state else ''
            dp_data = f"\n📅 *Дата:* {order['departure_date']}\n" if order['departure_date'] and order[
                'role'] == 'traveler' else "\n"
            text = \
                f"ID: {order['id']}\n" \
                f"Тип: {order_type}" \
                f"*{header_text}*" \
                f"{curr_traveler_is_executor_text}" \
                f"{dp_data}" \
                f"🛫 *Откуда:* {str(order['flight_route']).split(' - ')[0]}\n" \
                f"🛬 *Куда:* {str(order['flight_route']).split(' - ')[1]}\n" \
                f"✒ *Комментарий*: {order['comment']}\n"
            if DEBUG_MODE:
                debug_text = \
                    f"\n*DEBUG INFO:\n" \
                    f"contractor_id: {order['contractor_id']}\n" \
                    f"customer_id: {order['customer_id']}\n" \
                    f"date: {order['departure_date']}\n" \
                    f"flight_route: {order['departure_country']}|{order['departure_city']} - {order['arrival_country']}|{order['arrival_city']}*"
                text += debug_text
            IK = types.InlineKeyboardMarkup(row_width=1)
            try:
                if order['customer_id'] != user_id:
                    check_phone = user['phone'] if user else False
                    if order['state'] == OrderStates.order_accepted.state and check_phone:
                        if order['role'] == 'sender':
                            IK.insert(types.InlineKeyboardButton('🔼Связаться',
                                                                 callback_data=f"{order['id']}_order-execute"))
                        if order['role'] == 'traveler':
                            IK.insert(types.InlineKeyboardButton('🔼Связаться',
                                                                 callback_data=f"{order['id']}_customer-asks"))
                    if role == 'contractor':
                        if order['contractor_id']:
                            IK.insert(types.InlineKeyboardButton('✅ Завершить',
                                                                 callback_data=f"{order['id']}_contractor-completes-delivery"))
                            IK.insert(types.InlineKeyboardButton('❌ Отменить',
                                                                 callback_data=f"{order['id']}_contractor-cancels-delivery"))
                    elif role == 'customer':
                        pass
            except KeyError:
                pass
            mess = \
                {
                    'text': text,
                    'parse_mode': types.ParseMode.MARKDOWN,
                    'reply_markup': IK.to_python(),
                }
            prepared_messages.append(mess)
        await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
        await PaginationStates.step.set()
        await dp.current_state(chat=user_id, user=user_id).update_data(
            {
                'prepared_messages': prepared_messages,
                'page_index': 0,
                'user_id': user_id,
                'back_callback': back_callback,
                'contact_text': contact_text
            })
        await answer_with_pagination(user_id, 0)
    else:
        el_text = f"""🤫**По Вашему маршруту объявлений не найдено
Мы пришлем Вам уведомление, когда появится** 😌

*Пока можете пообщаться в нашем уютном чате*:
👉 [Cсылка]({group_chat_LINK_MD})"""
        else_text = 'Активные объявления отсутствуют❗' if back_callback != 'ad-search' \
            else el_text
        message = await bot.send_message(user_id, else_text, parse_mode=types.ParseMode.MARKDOWN)
        msg_ids = str(message.message_id)
        await navigation_menu(user_id, cb=f"{user_id}_{back_callback}", messages_id=msg_ids)


async def show_COMPLETED_orders_message_IK(user_id: int, role: str, back_callback: str):
    res = typing.Any
    values = [user_id, OrderStates.order_completed.state]
    if role == 'customer':
        res = await fetchmany(
            '''SELECT * FROM bot."order" WHERE customer_id = $1 AND state = $2  ORDER BY create_time''', values)
    elif role == 'contractor':
        res = await fetchmany(
            '''SELECT * FROM bot."order" WHERE contractor_id = $1 AND state = $2  ORDER BY create_time''', values)
    msg_list = []
    msg_ids = str()
    prepared_messages = []
    if len(res) > 0:
        for order in res:
            await asyncio.sleep(MESSAGE_DELAY)
            contractor = await fetchone_user(order['contractor_id'])
            customer = await fetchone_user(order['customer_id'])
            dp_data = f"*Дата:* {order['departure_date']}\n" \
                if order['departure_date'] and role == 'customer' else ""
            text = \
                f"ID: {order['id']}\n" \
                f"*Отправил:* {customer['first_name']} {customer['last_name']}\n" \
                f"*Доставил:* {contractor['first_name']} {contractor['last_name']}\n" \
                f"{dp_data}" \
                f"*Вылет:* {order['departure_country']} - {order['departure_city']}\n" \
                f"*Прилет:* {order['arrival_country']} - {order['arrival_city']}\n" \
                f"*Комментарий:* {order['comment']}"
            mess = \
                {
                    'text': text,
                    'parse_mode': types.ParseMode.MARKDOWN,
                    'reply_markup': None,
                }
            prepared_messages.append(mess)
        await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
        await PaginationStates.step.set()
        await dp.current_state(chat=user_id, user=user_id).set_data(
            {
                'prepared_messages': prepared_messages,
                'page_index': 0,
                'user_id': user_id,
                'back_callback': back_callback,
                'contact_text': None
            })
        await answer_with_pagination(user_id, 0)
    else:
        message = await bot.send_message(user_id, 'Завершенные объявления отсутствуют❗')
        msg_list.append(message.message_id)
        for msg in msg_list:
            msg_ids += f"{msg},"
        if role == 'contractor':
            await navigation_menu(user_id, cb=f"{user_id}_contractor-account", messages_id=msg_ids)
        elif role == 'customer':
            await navigation_menu(user_id, cb=f"{user_id}_customer-account", messages_id=msg_ids)


async def set_order_EXECUTOR_message_IK(user_id: int, order_id: int):
    """
    By clicking on the "⬆Contact" button, the announcement of the parcel disappears from the search and both
    receive notifications that the parcel is "In progress". But the travel announcement in the search remains.
    """
    await delete_message(user_id, await get_last_message(user_id))
    q_0 = await fetchone_order(order_id)
    customer_id = q_0['customer_id']
    await executeone('''UPDATE bot."order" SET contractor_id = $2 WHERE id = $1''', [order_id, user_id])
    q_1 = await fetchone_order(order_id)
    contractor_id = q_1['contractor_id']
    await executeone('''UPDATE bot."order" SET state = $2 WHERE id = $1''', [order_id, OrderStates.order_in_work.state])
    sender = await fetchone_user(customer_id)
    traveler = await fetchone_user(contractor_id)
    sender_username = f"@{sender['username']}"
    traveler_username = f"@{traveler['username']}"

    order = await fetchone_order(order_id)
    ct_flights = typing.Any
    if len(order) > 0:
        ct_flights = await fetchone('''SELECT * FROM bot."order" WHERE customer_id = $1 AND flight_route = $2''',
                                    [contractor_id, order['flight_route']])

    ct_text = f"""🔔 Вы доставляете отправление № {order_id}.

Информация об отправителе:
Имя: {sender['first_name']} {sender['last_name']}
Никнейм: {f"Номер телефона: {sender['phone']}" if not sender_username else sender_username}

🛫 Маршрут: {order['departure_city']} - {order['arrival_city']}
✒ Комментарий: {order['comment']}

Нажмите на никнейм, чтобы связаться👍

Чтобы завершить заказ перейдите:
"👤Мой аккаунт" -> "✈ Мои путешествия"""

    cs_text = f"""🔔 Ваше отправление № {order_id} доставит:

Имя: {traveler['first_name']} {traveler['last_name']}
Никнейм: {f"Номер телефона: {traveler['phone']}" if not traveler_username else traveler_username}

🛫 Маршрут: {order['departure_city']} - {order['arrival_city']}
✒ Комментарий: {order['comment']}

Нажмите на никнейм, чтобы связаться👍

Ваше объявление:
🛫 Маршрут: {ct_flights['departure_city']} - {ct_flights['arrival_city']}
✒ Комментарий: {ct_flights['comment']}

Чтобы завершить или удалить объявление перейдите:
"👤Мой аккаунт" -> "📦 Мои Отправления"""

    msg_1 = await bot.send_message(contractor_id, ct_text, parse_mode=types.ParseMode.MARKDOWN)
    await bot.pin_chat_message(chat_id=contractor_id, message_id=msg_1.message_id, disable_notification=False)
    await main_menu_message_IK(contractor_id)

    msg_2 = await bot.send_message(customer_id, cs_text, parse_mode=types.ParseMode.MARKDOWN)
    await bot.pin_chat_message(chat_id=customer_id, message_id=msg_2.message_id, disable_notification=False)
    await main_menu_message_IK(customer_id)


async def set_ORDER_STATUS(order_id: int, state: str, role: str, cb_data: str = None):
    order = await fetchone_order(order_id)
    if len(order) > 0:
        contractor_id = order['contractor_id']
        customer_id = order['customer_id']
        if contractor_id:
            opposite_order = await fetchone(
                '''SELECT id FROM bot."order" WHERE customer_id = $1 AND flight_route = $2 AND state != $3''',
                [contractor_id, order['flight_route'], state])
            if len(opposite_order) > 0:
                values = [
                    opposite_order['id'],
                    OrderStates.order_accepted.state if cb_data == 'contractor-cancels-delivery'
                                                        or cb_data == 'contractor-cancels-delivery' else OrderStates.order_terminated.state,
                    customer_id if state == OrderStates.order_accepted.state else None
                ]
                await executeone('''UPDATE bot."order" SET state = $2, contractor_id = $3 WHERE id = $1''', values)
            if role == 'contractor' and state == OrderStates.order_terminated.state:
                await executeone('''UPDATE bot."order" SET state = $2 WHERE id = $1''',
                                 [order_id, OrderStates.order_accepted.state])
                await executeone('''UPDATE bot."order" SET contractor_id = $2 WHERE id = $1''', [order_id, None])
        if role == 'contractor':
            contractor_text = f'🔔*Объявление ID: {order_id} завершено*' if cb_data != 'contractor-cancels-delivery' \
                else f'🔔*Объявление ID: {order_id} отменено*'
            if contractor_id and contractor_text:
                await bot.send_message(contractor_id, contractor_text, parse_mode=types.ParseMode.MARKDOWN)
            await bot.send_message(customer_id, contractor_text, parse_mode=types.ParseMode.MARKDOWN)


async def cancels_ORDER(order_id: int, state: str, role: str):
    f_order = await fetchone_order(order_id)
    if len(f_order) > 0:
        contractor_id = f_order['contractor_id']
        customer_id = f_order['customer_id']
        text = f'🔔*Объявление ID: {order_id} отменено*'
        if contractor_id:
            s_order = await fetchone(
                '''SELECT id, role FROM bot."order" WHERE customer_id = $1 AND flight_route = $2 AND state != $3''',
                [contractor_id, f_order['flight_route'], state])
            if len(s_order) > 0:
                _state = OrderStates.order_accepted.state if role == 'contractor' else state
                query = '''UPDATE bot."order" SET state = $2, contractor_id = $3 WHERE id = $1'''
                await executeone(query, [s_order['id'], OrderStates.order_accepted.state if role == 'customer' and s_order['role'] else _state, None])
                await executeone(query, [order_id, _state, f_order['contractor_id'] if role == 'customer' else None])
                await bot.send_message(contractor_id, text, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await executeone('''UPDATE bot."order" SET state = $2 WHERE id = $1''', [order_id, state])
        await bot.send_message(customer_id, text, parse_mode=types.ParseMode.MARKDOWN)


async def contractor_completes_ORDER(order_id: int, state: str):
    f_order = await fetchone_order(order_id)
    if len(f_order) > 0:
        contractor_id = f_order['contractor_id']
        customer_id = f_order['customer_id']
        text = f'🔔*Объявление ID: {order_id} завершено*'
        if contractor_id:
            s_order = await fetchone(
                '''SELECT id FROM bot."order" WHERE customer_id = $1 AND flight_route = $2 AND state != $3''',
                [contractor_id, f_order['flight_route'], state])
            if len(s_order) > 0:
                await executeone('''UPDATE bot."order" SET state = $2 WHERE id = $1''',
                                 [order_id, state])
        else:
            await executeone('''UPDATE bot."order" SET state = $2 WHERE id = $1''', [order_id, state])
        await bot.send_message(contractor_id, text, parse_mode=types.ParseMode.MARKDOWN)
        await bot.send_message(customer_id, text, parse_mode=types.ParseMode.MARKDOWN)


async def order_CONFIRM_message_IK(user_id: int, order_id: int, role: str, state: str):
    order = await fetchone_order(order_id)
    text = str()

    await executeone('''UPDATE bot."order" SET state = $2 WHERE id = $1''', [order_id, state])
    if state == OrderStates.order_accepted.state:
        if role == 'contractor':
            await executeone('''UPDATE bot.contractor SET state = $2 WHERE user_id = $1''', [user_id, state])
        elif role == 'customer':
            await executeone('''UPDATE bot.customer SET state = $2 WHERE user_id = $1''', [user_id, state])
        text += f"Объявление {'о путешествии' if role == 'contractor' else 'об отправлении'} ID: {order_id} создано.\n" \
                f"Маршрут: *{order['flight_route']}*"
    elif state == OrderStates.order_terminated.state:
        await terminate_order_message_IK(user_id, order_id)
        text += "Объявление удалено"
    await bot.send_message(user_id, text, reply_markup=types.ReplyKeyboardRemove(), parse_mode=types.ParseMode.MARKDOWN)
    if state == OrderStates.order_accepted.state:
        if role == 'customer':
            await ad_search_menu_message_IK(user_id)
        elif role == 'contractor':
            await ad_search_menu_message_IK(user_id)
    if state == OrderStates.order_terminated.state:
        await main_menu_message_IK(user_id)
