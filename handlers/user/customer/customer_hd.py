import asyncio
from datetime import datetime

from aiogram import types

from config import MESSAGE_DELAY, find_companion_TEXT
from core import dp
from data.database.database import executeone
from data.database.db_api import insert_customer, fetchone_last_order_id
from keyboards.user.common.common_inline_kb import phone_verification_message_IK, get_number_active_orders
from keyboards.user.common.flight_route_kb import START_departure_country_message_IK
from keyboards.user.customer.customer_kb import sender_ACCOUNT_ORDERS_message_IK
from keyboards.user.order.common_order_kb import show_COMPLETED_orders_message_IK, show_orders_BY_STATE_message_IK, \
    cancels_ORDER
from keyboards.user.order.customer_order_kb import customer_asks_order_executor_info_message_IK
from states.OrderStates import OrderStates
from utils.chat_mgmt import delete_message, get_last_message


def reg_contractor_handlers():
    dp.register_callback_query_handler(FIND_companion,
                                       lambda c: str(c.data).split('_')[1] == "find-companion", state='*')
    dp.register_callback_query_handler(customer_account,
                                       lambda c: str(c.data).split('_')[1] == "customer-account", state='*')
    dp.register_callback_query_handler(customer_get_NEARBY_contractors,
                                       lambda c: str(c.data).split('_')[1] == "get-nearby-customers", state='*')
    dp.register_callback_query_handler(customer_CURRENT_orders,
                                       lambda c: str(c.data).split('_')[1] == "customer-current-orders", state='*')
    dp.register_callback_query_handler(customer_completed_orders,
                                       lambda c: str(c.data).split('_')[1] == "customer-completed-orders", state='*')
    dp.register_callback_query_handler(customer_asks_order_executor_info,
                                       lambda c: str(c.data).split('_')[1] == "customer-asks", state='*')
    dp.register_callback_query_handler(customer_CANCELS_order,
                                       lambda c: str(c.data).split('_')[1] == "customer-deletes-order", state='*')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"find-companion", state='*')
async def FIND_companion(callback_query: types.CallbackQuery):
    phone_verification = await phone_verification_message_IK(callback_query.from_user.id, 'customer')
    has_active_orders = await get_number_active_orders(callback_query.from_user.id, 'customer')
    if phone_verification and has_active_orders:
        await delete_message(callback_query.from_user.id, await get_last_message(callback_query.from_user.id),
                             MESSAGE_DELAY)
        order_id = await fetchone_last_order_id()
        await insert_customer(callback_query.from_user)
        q_0 = '''INSERT INTO bot."order"(id, state, customer_id, role, create_time) VALUES($1,$2,$3,$4,$5)'''
        values = [order_id, OrderStates.order_start_creating.state, callback_query.from_user.id, 'sender',
                  datetime.timestamp(datetime.now())]
        await executeone(q_0, values)
        await START_departure_country_message_IK(callback_query.from_user.id, 'customer', order_id, find_companion_TEXT)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"customer-account", state='*')
async def customer_account(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await sender_ACCOUNT_ORDERS_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "customer-current-orders", state='*')
async def customer_CURRENT_orders(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await show_orders_BY_STATE_message_IK(callback_query.from_user.id, 'customer', OrderStates.order_in_work.state,
                                          'customer-account')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "customer-completed-orders", state='*')
async def customer_completed_orders(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await show_COMPLETED_orders_message_IK(callback_query.from_user.id, 'customer', 'customer-account')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "customer-asks", state='*')
async def customer_asks_order_executor_info(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[0])
    spl = callback_query.data.split(':')
    state = None
    if len(spl) > 1:
        state = spl[0].split('_')[2] + ":" + spl[1]
    await customer_asks_order_executor_info_message_IK(callback_query, order_id, state)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "customer-deletes-order", state='*')
async def customer_CANCELS_order(callback_query: types.CallbackQuery):
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()
    order_id = int(callback_query.data.split('_')[0])
    await cancels_ORDER(order_id, OrderStates.order_terminated.state, 'customer')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"get-nearby-contractors", state='*')
async def customer_get_NEARBY_contractors(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await show_orders_BY_STATE_message_IK(callback_query.from_user.id, 'customer', OrderStates.order_accepted.state,
                                          'ad-search')
