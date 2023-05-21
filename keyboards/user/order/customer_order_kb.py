from aiogram import types

from core import bot
from data.database.database import fetchone
from data.database.db_api import fetchone_user
from states.OrderStates import OrderStates


async def customer_asks_order_executor_info_message_IK(callback_query: types.CallbackQuery, order_id: int,
                                                       state: str = None):
    res = await fetchone('''SELECT * FROM bot."order" WHERE id = $1 AND state = $2''',
                         [order_id, state if state else OrderStates.order_accepted.state])
    text = str()
    if len(res) > 0:
        ct_id = res['contractor_id']
        res_2 = await fetchone(
            '''SELECT customer_id FROM bot."order" WHERE customer_id = $1 AND state = $2 AND flight_route = $3''',
            [res['customer_id'], state if state else OrderStates.order_accepted.state, res['flight_route']])
        if ct_id and ct_id != callback_query.from_user.id:
            user = await fetchone_user(ct_id)
            text = f"Посылку доставляет:\n" \
                   f"👤Имя: {user['first_name']} {user['last_name']}\n" \
                   f"✍ Ник: @{user['username']}"
        elif ct_id == callback_query.from_user.id:
            if len(res) > 0:
                cs_id = res_2['customer_id']
                if cs_id:
                    user = await fetchone_user(cs_id)
                    text = f"Вы доставляете эту посылку.\n" \
                           f"Отправитель:\n" \
                           f"👤Имя: {user['first_name']} {user['last_name']}\n" \
                           f"✍ Ник: @{user['username']}"
        elif ct_id is None:
            user = await fetchone_user(res_2['customer_id'])
            text = f"Путешественник:\n" \
                   f"👤Имя: {user['first_name']} {user['last_name']}\n" \
                   f"✍ Ник: @{user['username']}"
        await bot.answer_callback_query(callback_query.id, text, show_alert=True)
