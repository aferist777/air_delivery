from aiogram import types

from config import MESSAGE_DELAY
from core import bot
from data.database.database import executeone, fetchmany
from keyboards.user.common.common_inline_kb import main_menu_message_IK
from states.OrderStates import OrderStates
from utils.chat_mgmt import get_last_message, delete_message


async def terminate_order_message_IK(user_id: int | None, order_id: int):
    if order_id:
        q_1 = '''UPDATE bot."order" SET state = $2 WHERE id = $1'''
        await executeone(q_1, [order_id, OrderStates.order_terminated.state])
    await main_menu_message_IK(user_id)


async def sender_ACCOUNT_ORDERS_message_IK(user_id: int):
    await delete_message(user_id, await get_last_message(user_id), MESSAGE_DELAY)
    text = """📘Ваши опубликованные объявления отправлений.

Нажмите “Отменить”, если отправление уже завершено или Вы передумали:"""
    values = [user_id, OrderStates.order_accepted.state, OrderStates.order_in_work.state]
    res = await fetchmany(
        '''SELECT * FROM bot."order" WHERE customer_id = $1 AND role = 'sender' AND (state = $2 or state = $3) ORDER BY create_time''',
        values)
    msg_list = []
    msg_FIRST = await bot.send_message(user_id, text, parse_mode=types.ParseMode.MARKDOWN)
    msg_list.append(msg_FIRST.message_id)
    if len(res) > 0:
        for i, order in enumerate(res):
            order_type = 'Отправление\n' if order['role'] == 'sender' else 'Путешествие\n'
            header_text = 'Ваше объявление.\n' if order['customer_id'] == user_id else ''
            text = \
                f"{i + 1}.\n\n" \
                f"ID: {order['id']}\n" \
                f"Тип: *{order_type}*" \
                f"*{header_text}*" \
                f"\n*Маршрут:* {order['flight_route']}\n" \
                f"*Описание:* {order['comment']}\n" \
                f"*Статус:* {await formate_order_status(order['state'])}"
            IK = types.InlineKeyboardMarkup(row_width=1)
            if order['contractor_id']:
                IK.insert(types.InlineKeyboardButton('Подробнее',
                                                     callback_data=f"{order['id']}_customer-asks_{order['state']}"))
            IK.insert(types.InlineKeyboardButton('❌ Отменить', callback_data=f"{order['id']}_customer-deletes-order"))
            msg_LAST = await bot.send_message(user_id, text, parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK)
            if i == len(res) - 1:
                msg_list.append(msg_LAST.message_id)
        msg_ids = "-".join(map(str, msg_list))
    else:
        msg_FIRST = await bot.send_message(user_id, 'Активные объявления отсутствуют❗')
        msg_list.append(msg_FIRST.message_id + 1)
        msg_ids = "-".join(map(str, msg_list))
    IK_2 = types.InlineKeyboardMarkup(row_width=2)
    """IK_2.insert(types.InlineKeyboardButton('♻️Активные отправления',
                                           callback_data=f"{user_id}_customer-current-orders_{msg_ids}"))"""
    IK_2.insert(types.InlineKeyboardButton('Доставленные посылки',
                                           callback_data=f"{user_id}_customer-completed-orders_{msg_ids}"))
    IK_2.row(types.InlineKeyboardButton('👈 Назад', callback_data=f"{user_id}_back-to-account_{msg_ids}"),
             types.InlineKeyboardButton('👈️ В меню', callback_data=f"{user_id}_back-to-menu_{msg_ids}"))
    await bot.send_message(user_id, 'Меню отправлений', reply_markup=IK_2)


async def formate_order_status(state: str):
    return state.split(':')[1].replace('_', ' ').replace('order', '').upper()
