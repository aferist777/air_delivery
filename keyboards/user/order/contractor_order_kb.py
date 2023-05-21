from aiogram import types

from core import bot
from data.database.database import fetchone
from data.database.db_api import fetchone_user
from states.OrderStates import OrderStates


async def contractor_asks_order_customer_info_message_IK(callback_query: types.CallbackQuery, order_id: int,
                                                         state: str = None):
    res = await fetchone('''SELECT * FROM bot."order" WHERE id = $1 AND state = $2''',
                         [order_id, state if state else OrderStates.order_accepted.state])
    if len(res) > 0:
        user = await fetchone_user(res['customer_id'])
        if len(user) > 0:
            text = f"Информация о путешественнике:\n" \
                   f"👤Имя: {user['first_name']} {user['last_name']}\n" \
                   f"✍ Ник: @{user['username']}"
            await bot.answer_callback_query(callback_query.id, text, show_alert=True)
