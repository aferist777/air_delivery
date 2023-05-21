import asyncio
from datetime import datetime

from aiogram import types
from aiogram_calendar import SimpleCalendar

from config import MESSAGE_DELAY, taking_flight_TEXT
from core import bot
from core import dp
from data.database.database import executeone
from data.database.db_api import insert_contractor, fetchone_last_order_id
from keyboards.user.common.common_inline_kb import phone_verification_message_IK, get_number_active_orders
from keyboards.user.common.common_reply_kb import cancel_button_message_RK
from keyboards.user.contractor.contractor_kb import traveler_ACCOUNT_ORDERS_message_IK
from keyboards.user.order.common_order_kb import show_COMPLETED_orders_message_IK, show_orders_BY_STATE_message_IK, \
    cancels_ORDER, contractor_completes_ORDER
from keyboards.user.order.contractor_order_kb import contractor_asks_order_customer_info_message_IK
from states.ContractorStates import ContractorStates
from states.OrderStates import OrderStates
from utils.chat_mgmt import delete_message, get_last_message


def reg_customer_handlers():
    dp.register_callback_query_handler(TAKING_flight,
                                       lambda c: str(c.data).split('_')[1] == "taking-flight", state='*')
    dp.register_callback_query_handler(contractor_account,
                                       lambda c: str(c.data).split('_')[1] == "contractor-account", state='*')
    dp.register_callback_query_handler(contractor_get_NEARBY_customers,
                                       lambda c: str(c.data).split('_')[1] == "get-nearby-contractors", state='*')
    dp.register_callback_query_handler(contractor_CURRENT_deliveries,
                                       lambda c: str(c.data).split('_')[1] == "contractor-current-deliveries",
                                       state='*')
    dp.register_callback_query_handler(contractor_completed_deliveries,
                                       lambda c: str(c.data).split('_')[1] == "contractor-completed-deliveries",
                                       state='*')
    dp.register_callback_query_handler(contractor_asks_order_customer_info,
                                       lambda c: str(c.data).split('_')[1] == "contractor-asks",
                                       state='*')
    dp.register_callback_query_handler(contractor_COMPLETES_delivery,
                                       lambda c: str(c.data).split('_')[1] == "contractor-completes-delivery",
                                       state='*')
    dp.register_callback_query_handler(contractor_CANCELS_travel,
                                       lambda c: str(c.data).split('_')[1] == "contractor-cancels-delivery", state='*')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "taking-flight", state='*')
async def TAKING_flight(callback_query: types.CallbackQuery):
    phone_verification = await phone_verification_message_IK(callback_query.from_user.id, 'contractor')
    has_active_orders = await get_number_active_orders(callback_query.from_user.id, 'contractor')
    if phone_verification and has_active_orders:
        await delete_message(callback_query.from_user.id, await get_last_message(callback_query.from_user.id),
                             MESSAGE_DELAY)
        order_id = await fetchone_last_order_id()
        await insert_contractor(callback_query.from_user)
        q_0 = '''INSERT INTO bot."order"(id, state, customer_id, role, create_time) VALUES($1,$2,$3,$4,$5)'''
        values = [order_id, OrderStates.order_start_creating.state, callback_query.from_user.id, 'traveler',
                  datetime.timestamp(datetime.now())]
        await executeone(q_0, values)
        msg_1 = await bot.send_message(callback_query.from_user.id, taking_flight_TEXT,
                                       parse_mode=types.ParseMode.MARKDOWN,
                                       reply_markup=await SimpleCalendar().start_calendar())
        msg_2 = await bot.send_message(callback_query.from_user.id,
                                       'Для отмены создания заказа нажмите кнопку снизу',
                                       parse_mode=types.ParseMode.MARKDOWN,
                                       reply_markup=await cancel_button_message_RK())
        await ContractorStates.set_departure_date.set()
        await dp.current_state(chat=callback_query.from_user.id, user=callback_query.from_user.id).set_data(
            {
                'order_id': order_id,
                'calendar_msg_ids': f"{msg_1.message_id},{msg_2.message_id}"
            })


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "contractor-account", state='*')
async def contractor_account(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await traveler_ACCOUNT_ORDERS_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[0] == "contractor-current-deliveries", state='*')
async def contractor_CURRENT_deliveries(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await show_orders_BY_STATE_message_IK(callback_query.from_user.id, 'contractor', OrderStates.order_in_work.state,
                                          'contractor-account')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[0] == "contractor-completed-deliveries", state='*')
async def contractor_completed_deliveries(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await show_COMPLETED_orders_message_IK(callback_query.from_user.id, 'contractor', 'contractor-account')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "contractor-asks", state='*')
async def contractor_asks_order_customer_info(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[0])
    spl = callback_query.data.split(':')
    state = None
    if len(spl) > 1:
        state = spl[0].split('_')[2] + ":" + spl[1]
    await contractor_asks_order_customer_info_message_IK(callback_query, order_id, state)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "contractor-completes-delivery", state='*')
async def contractor_COMPLETES_delivery(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[0])
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()
    await contractor_completes_ORDER(order_id, OrderStates.order_completed.state)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "contractor-cancels-delivery", state='*')
async def contractor_CANCELS_travel(callback_query: types.CallbackQuery):
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()
    order_id = int(callback_query.data.split('_')[0])
    await cancels_ORDER(order_id, OrderStates.order_terminated.state, 'contractor')


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"get-nearby-customers", state='*')
async def contractor_get_NEARBY_customers(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await show_orders_BY_STATE_message_IK(callback_query.from_user.id, 'contractor', OrderStates.order_accepted.state,
                                          'ad-search')
