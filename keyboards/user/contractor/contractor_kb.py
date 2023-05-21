import typing

from aiogram import types

from core import bot
from config import MESSAGE_DELAY
from data.database.database import fetchone, fetchmany
from keyboards.user.customer.customer_kb import formate_order_status
from states.OrderStates import OrderStates
from utils.chat_mgmt import delete_message, save_message, get_last_message


async def checking_contractor_orders_in_progress_message(user_id: int, role: str):
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    values = [user_id, OrderStates.order_in_work.state]
    orders = await fetchone('''SELECT count(*) FROM bot."order"
                 WHERE customer_id = $1 AND state = $2 ORDER BY create_time''', values)
    if orders['count'] != 0:
        acc_text = 'отправителя' if role == 'customer' else 'путешественника'
        customer_text = 'ваши заказы доставляются'
        contractor_text = 'вы не завершите заказ или его не отменит отправитель'
        text = customer_text if role == 'customer' else contractor_text
        message = await bot.send_message(user_id, f'❗*Вы не сможете удалить аккаунт *_{acc_text}_* пока {text}*❗',
                                         parse_mode=types.ParseMode.MARKDOWN_V2)
        await save_message(user_id, message.message_id)
        return False
    else:
        return True


async def traveler_ACCOUNT_ORDERS_message_IK(user_id: int):
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    h_text = """📗 Ваши опубликованные объявления путешествий.

Нажмите “Отменить”, если путешествие уже завершено или Вы передумали:"""
    res = []
    values = [user_id, OrderStates.order_accepted.state, OrderStates.order_in_work.state]
    res_1: list[dict] = await fetchmany('''SELECT * FROM bot."order"
                WHERE customer_id = $1 AND role = 'traveler' AND (state = $2 or state = $3) ORDER BY create_time''',
                                        values)

    res_2: list[dict] = await fetchmany('''SELECT * FROM bot."order"
                WHERE contractor_id = $1 AND role = 'sender' AND (state = $2 or state = $3) ORDER BY create_time''',
                                        values)
    if len(res_1) > 0:
        res.extend(res_1)

    if len(res_2) > 0:
        res.extend(res_2)

    msg_list = []
    _msg_FIRST = await bot.send_message(user_id, h_text, parse_mode=types.ParseMode.MARKDOWN)
    last_user_msg_id = int(await get_last_message(user_id))
    msg_FIRST = last_user_msg_id if _msg_FIRST.message_id - last_user_msg_id > 1 else _msg_FIRST.message_id
    msg_list.append(msg_FIRST)
    if len(res) > 0:
        for i, order in enumerate(res):
            order_type = 'Отправление\n' if order['role'] == 'sender' else 'Путешествие\n'
            index_text = f"{i + 1}.\n\n" if order['role'] == 'traveler' else ''
            header_text = 'Ваше объявление.\n' if order['customer_id'] == user_id else ''
            dp_data = f"\n*Дата:* {order['departure_date']}\n" \
                if order['departure_date'] is not None and order['role'] == 'traveler' else "\n"
            text = \
                f"{index_text}" \
                f"ID: {order['id']}\n" \
                f"Тип: *{order_type}*" \
                f"*{header_text}*" \
                f"{dp_data}" \
                f"*Маршрут:* {order['flight_route']}\n" \
                f"*Описание:* {order['comment']}\n" \
                f"*Статус:* {await formate_order_status(order['state'])}"
            check_inwork_state = await fetchone(
                '''SELECT count(*) FROM bot."order" WHERE contractor_id = $1 and state = 'OrderStates:order_in_work' ''',
                [order['customer_id']])
            IK = types.InlineKeyboardMarkup(row_width=2)
            cancel_btn = types.InlineKeyboardButton('❌ Отменить',
                                                    callback_data=f"{order['id']}_contractor-cancels-delivery")
            if order['contractor_id']:
                IK.row(types.InlineKeyboardButton('✅ Завершить',
                                                  callback_data=f"{order['id']}_contractor-completes-delivery"),
                       types.InlineKeyboardButton('Подробнее',
                                                  callback_data=f"{order['id']}_customer-asks_{order['state']}"))
                IK.row(cancel_btn)
            elif not check_inwork_state['count'] > 0:
                IK.row(cancel_btn)
            msg_LAST = await bot.send_message(user_id, text, parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK)
            if i == len(res) - 1:
                msg_list.append(msg_LAST.message_id)
        msg_ids = "-".join(map(str, msg_list))
    else:
        msg_LAST = await bot.send_message(user_id, 'Активные объявления отсутствуют❗')
        msg_list.append(msg_LAST.message_id + 1)
        msg_ids = "-".join(map(str, msg_list))
    IK_2 = types.InlineKeyboardMarkup(row_width=2)
    """IK_2.insert(types.InlineKeyboardButton('♻️Активные доставки',
                                           callback_data=f"{user_id}_contractor-current-deliveries_{msg_ids}"))"""
    IK_2.insert(types.InlineKeyboardButton('Завершенные доставки',
                                           callback_data=f"{user_id}_contractor-completed-deliveries_{msg_ids}"))
    IK_2.row(types.InlineKeyboardButton('👈 Назад', callback_data=f"{user_id}_back-to-account_{msg_ids}"),
             types.InlineKeyboardButton('👈️ В меню', callback_data=f"{user_id}_back-to-menu_{msg_ids}"))
    await bot.send_message(user_id, 'Меню путешествий', parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK_2)
