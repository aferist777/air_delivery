import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

from config import MESSAGE_DELAY, MIN_BIO_CHARS, MAX_BIO_CHARS
from core import dp
from data.database.database import executeone
from keyboards.user.common.common_inline_kb import my_account_message_IK
from states.UserStates import UserStates
from utils.chat_mgmt import get_last_message, delete_message, save_message


def reg_account_commands_handler():
    dp.register_message_handler(user_photo, commands=['set_photo'])
    dp.register_message_handler(traveler_bio, commands=['set_traveler_bio'])
    dp.register_message_handler(sender_bio, commands=['set_sender_bio'])
    dp.register_message_handler(set_user_photo, state=UserStates.set_photo, content_types=[types.ContentType.PHOTO, types.ContentType.TEXT])
    dp.register_message_handler(set_traveler_bio, state=UserStates.set_traveler_bio)
    dp.register_message_handler(set_sender_bio, state=UserStates.set_sender_bio)


@dp.message_handler(commands=['set_photo'])
async def user_photo(message: types.Message):
    msg = await message.answer('Отправьте боту Вашу фотографию')
    await save_message(message.from_user.id, msg.message_id)
    await UserStates.set_photo.set()


@dp.message_handler(commands=['set_traveler_bio'])
async def traveler_bio(message: types.Message):
    msg = await message.answer(f'Чтобы изменить информацию о Вас как путешественнике скопируйте текст,'
                               f' нажав на него или введите новый.')
    await save_message(message.from_user.id, msg.message_id)
    await UserStates.set_traveler_bio.set()


@dp.message_handler(commands=['set_sender_bio'])
async def sender_bio(message: types.Message):
    msg = await message.answer(f'Чтобы изменить информацию о Вас как отправителе скопируйте текст,'
                               f' нажав на него или введите новый.')
    await save_message(message.from_user.id, msg.message_id)
    await UserStates.set_sender_bio.set()


@dp.message_handler(state=UserStates.set_photo, content_types=[types.ContentType.PHOTO, types.ContentType.TEXT])
async def set_user_photo(message: types.Message, state: FSMContext):
    await delete_message(message.from_user.id, await get_last_message(message.from_user.id), MESSAGE_DELAY)
    async with state.proxy():
        check_loopback = message.text not in ['/start', '/set_photo']
        if message.content_type == 'photo' and check_loopback:
            q = '''UPDATE bot.user SET photo = $2 WHERE user_id = $1'''
            await executeone(q, [message.from_user.id, message.photo[-2].file_id])
            msg = await message.answer('Фотография обновлена')
            await save_message(message.from_user.id, msg.message_id)
            await state.finish()
            await asyncio.sleep(MESSAGE_DELAY)
            await my_account_message_IK(message.from_user.id)
        if not check_loopback:
            await state.finish()
            await my_account_message_IK(message.from_user.id)


@dp.message_handler(state=UserStates.set_traveler_bio)
async def set_traveler_bio(message: types.Message, state: FSMContext):
    await delete_message(message.from_user.id, await get_last_message(message.from_user.id), MESSAGE_DELAY)
    async with state.proxy():
        check_text_length = True if MAX_BIO_CHARS >= len(message.text) >= MIN_BIO_CHARS else False
        check_loopback = message.text not in ['/start', '/set_traveler_bio']
        text = message.text
        if text and check_text_length and check_loopback:
            q = '''UPDATE bot.user SET traveler_bio = $2 WHERE user_id = $1'''
            await executeone(q, [message.from_user.id, text])
            msg = await message.answer('Изменения сохранены')
            await save_message(message.from_user.id, msg.message_id)
            await state.finish()
            await asyncio.sleep(MESSAGE_DELAY)
            await my_account_message_IK(message.from_user.id)
        elif not check_text_length:
            msg = await message.answer(f'Количество символов должно быть от {MIN_BIO_CHARS} до {MAX_BIO_CHARS}')
            await save_message(message.from_user.id, msg.message_id)
        if not check_loopback:
            await state.finish()
            await my_account_message_IK(message.from_user.id)


@dp.message_handler(state=UserStates.set_sender_bio)
async def set_sender_bio(message: types.Message, state: FSMContext):
    await delete_message(message.from_user.id, await get_last_message(message.from_user.id), MESSAGE_DELAY)
    async with state.proxy():
        check_text_length = True if MAX_BIO_CHARS >= len(message.text) >= MIN_BIO_CHARS else False
        check_loopback = message.text not in ['/start', '/set_sender_bio']
        text = message.text
        if text and check_text_length and check_loopback:
            q = '''UPDATE bot.user SET sender_bio = $2 WHERE user_id = $1'''
            await executeone(q, [message.from_user.id, text])
            msg = await message.answer('Изменения сохранены')
            await save_message(message.from_user.id, msg.message_id)
            await state.finish()
            await asyncio.sleep(MESSAGE_DELAY)
            await my_account_message_IK(message.from_user.id)
        elif not check_text_length:
            msg = await message.answer(f'Количество символов должно быть от {MIN_BIO_CHARS} до {MAX_BIO_CHARS}')
            await save_message(message.from_user.id, msg.message_id)
        if not check_loopback:
            await state.finish()
            await my_account_message_IK(message.from_user.id)
