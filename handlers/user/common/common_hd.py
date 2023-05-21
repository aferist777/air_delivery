import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType

from config import MESSAGE_DELAY
from core import dp
from data.database.database import executeone
from keyboards.user.common.common_inline_kb import start_work_menu_message_IK, my_account_message_IK, \
    main_menu_message_IK, ad_search_menu_message_IK, important_info_message_IK
from keyboards.user.customer.customer_kb import terminate_order_message_IK
from states.UserStates import UserStates
from utils.chat_mgmt import delete_message


def reg_common_interface_handlers():
    dp.register_callback_query_handler(start_work, lambda c: str(c.data).split('_')[1] == "start-work", state='*')
    dp.register_callback_query_handler(ad_search, lambda c: str(c.data).split('_')[1] == "ad-search", state='*')
    dp.register_callback_query_handler(important_info, lambda c: str(c.data).split('_')[1] == "important-info", state='*')
    dp.register_callback_query_handler(my_account, lambda c: c.data == f"{c.from_user.id}_my-account", state='*')
    dp.register_callback_query_handler(back_to_account,
                                       lambda c: str(c.data).split('_')[1] == f"back-to-account", state='*')
    dp.register_callback_query_handler(back_to_menu,
                                       lambda c: str(c.data).split('_')[1] == f"back-to-menu", state='*')
    dp.register_callback_query_handler(back_to_start_work_menu,
                                       lambda c: str(c.data).split('_')[1] == f"back-to-start-work-menu", state='*')
    dp.register_callback_query_handler(cancel_flight_route,
                                       lambda c: str(c.data).split('_')[1] == f"cancel-flight-route")
    dp.register_message_handler(set_phone, state=UserStates.set_phone,
                                content_types=[ContentType.CONTACT, ContentType.TEXT])


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "start-work", state='*')
async def start_work(callback_query: types.CallbackQuery):
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()
    await start_work_menu_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "ad-search", state='*')
async def ad_search(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await ad_search_menu_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "important-info", state='*')
async def important_info(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await important_info_message_IK(callback_query.from_user.id)


@dp.message_handler(state=UserStates.set_phone, content_types=[ContentType.CONTACT, ContentType.TEXT])
async def set_phone(message: types.Message, state: FSMContext):
    async with state.proxy():
        check_loopback = message.text not in ['/start', '/set_photo']
        if hasattr(message.contact, 'phone_number') and check_loopback:
            q = '''UPDATE bot.user SET phone = $2 WHERE user_id = $1'''
            await executeone(q, [message.from_user.id, message.contact.phone_number])
            await state.finish()
            await start_work_menu_message_IK(message.from_user.id)
        elif not hasattr(message.contact, 'phone_number') and not message.text == '😑 Осмотреться':
            await message.answer("Для продолжения подтвердите отправку вашего номера")
        elif message.text == '😑 Осмотреться':
            await state.finish()
            await main_menu_message_IK(message.from_user.id)
        if not check_loopback:
            await state.finish()
            await my_account_message_IK(message.from_user.id)


@dp.callback_query_handler(lambda c: c.data == f"{c.from_user.id}_my-account", state='*')
async def my_account(callback_query: types.CallbackQuery):
    await my_account_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"back-to-account", state='*')
async def back_to_account(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await my_account_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"back-to-menu", state='*')
async def back_to_menu(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await main_menu_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"back-to-start-work-menu", state='*')
async def back_to_start_work_menu(callback_query: types.CallbackQuery):
    msg_ids = callback_query.data.split('_')[-1]
    if msg_ids:
        await delete_message(callback_query.from_user.id, msg_ids, MESSAGE_DELAY)
    else:
        await asyncio.sleep(MESSAGE_DELAY)
        await callback_query.message.delete()
    await start_work_menu_message_IK(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == f"cancel-flight-route", state='*')
async def cancel_flight_route(callback_query: types.CallbackQuery):
    raw = callback_query.data.split('_')[0]
    order_id = int(raw) if raw.isdigit() else None
    await terminate_order_message_IK(callback_query.from_user.id, order_id)
    await asyncio.sleep(MESSAGE_DELAY)
    await callback_query.message.delete()
