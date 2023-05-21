import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

from config import MESSAGE_DELAY
from core import dp, bot, is_admin
from keyboards.admin.admin_kb import countries_management_message_IK
from states.AdminStates import AdminStates


def reg_admin_handlers():
    dp.register_message_handler(admin, commands=['admin'])
    dp.register_callback_query_handler(countries_management, lambda c: c.data == "countries-management")
    dp.register_callback_query_handler(admin_update_country, lambda c: str(c.data).split('_')[1] == "update-country")
    dp.register_callback_query_handler(admin_add_country, lambda c: str(c.data).split('_')[1] == "add-country")
    dp.register_callback_query_handler(admin_delete_country, lambda c: str(c.data).split('_')[1] == "delete-country")
    dp.register_message_handler(update_country_state, state=AdminStates.update_country)
    dp.register_message_handler(add_country_state, state=AdminStates.add_country)
    dp.register_message_handler(delete_country_state, state=AdminStates.delete_country)


@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if await is_admin(message.from_user.id):
        await message.answer('...')
        # await set_my_commands(users_id=message.from_user.id, command_list=admin_commands)
        # await admin_panel_message_IK(message.from_user.id)


@dp.callback_query_handler(lambda c: c.data == "countries-management")
async def countries_management(callback_query: types.CallbackQuery):
    await countries_management_message_IK(callback_query.from_user.id)
    await callback_query.message.delete()
    await asyncio.sleep(MESSAGE_DELAY)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "update-country")
async def admin_update_country(callback_query: types.CallbackQuery):
    flag = callback_query.data.split('_')[-4]
    country_name_rus = callback_query.data.split('_')[-3]
    country_name_eng = callback_query.data.split('_')[-2]
    country_iso_code = callback_query.data.split('_')[-1]
    text = f"Обновление данных о стране:\n" \
           f"`iso_code={country_iso_code}, name_rus={country_name_rus}, name_eng={country_name_eng}, flag={flag}`\n" \
           f"Формат ввода:\n\n" \
           f"`iso_code=`двузначный код страны\n" \
           f"`name_rus=`название страны на русском\n" \
           f"`name_eng=`название страны с переводом на английский\n" \
           f"`flag=`эмодзи флага страны" \
           f"\n\nВнимание! Обязательные параметры iso\_code, name\_eng. *Параметры вводятся через ','*"
    await bot.send_message(callback_query.from_user.id, text, parse_mode=types.ParseMode.MARKDOWN)
    await AdminStates.update_country.set()
    await callback_query.message.delete()
    await asyncio.sleep(MESSAGE_DELAY)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "add-country")
async def admin_add_country(callback_query: types.CallbackQuery):
    text = f"Добавление города.\n" \
           f"Шаблон: `iso_code=, name_rus=, name_eng=, flag=`\n" \
           f"Формат ввода:\n\n" \
           f"`iso_code=`двузначный код страны\n" \
           f"`name_rus=`название страны на русском\n" \
           f"`name_eng=`название страны с переводом на английский\n" \
           f"`flag=`эмодзи флага страны" \
           f"\n\nВнимание! Обязательные параметры iso\_code, name\_eng. *Параметры вводятся через ','*"
    await bot.send_message(callback_query.from_user.id, text, parse_mode=types.ParseMode.MARKDOWN)
    await AdminStates.add_country.set()
    await callback_query.message.delete()
    await asyncio.sleep(MESSAGE_DELAY)


@dp.callback_query_handler(lambda c: str(c.data).split('_')[1] == "delete-country")
async def admin_delete_country(callback_query: types.CallbackQuery):
    text = f"Удаление города.\n" \
           f"Шаблон: `iso_code=, name_eng=`\n" \
           f"Формат ввода:\n\n" \
           f"`iso_code=`двузначный код страны\n" \
           f"`name_eng=`название страны с переводом на английский" \
           f"\n\nВнимание! Обязательные параметры iso\_code, name\_eng. *Параметры вводятся через ','*"
    await bot.send_message(callback_query.from_user.id, text, parse_mode=types.ParseMode.MARKDOWN)
    await AdminStates.delete_country.set()
    await callback_query.message.delete()
    await asyncio.sleep(MESSAGE_DELAY)


@dp.message_handler(state=AdminStates.update_country)
async def update_country_state(message: types.Message, state: FSMContext):
    async with state.proxy():
        try:
            try:
                as_json = {str(x).split('=')[0].replace(' ', ''): str(x).split('=')[1] for x in message.text.split(',')}
            except IndexError:
                as_json = None
            if as_json:
                upd_country_dict = dict()
                columns_dict = database['country'].columns_dict
                for key, val in as_json.items():
                    try:
                        if columns_dict[key]:
                            upd_country_dict.update({key: val if val != '' else None})
                    except KeyError:
                        pass
                if len(upd_country_dict) == len(columns_dict):
                    database['country'].upsert(upd_country_dict, pk='iso_code')
                    await message.answer('Изменения сохранены')
                    await state.finish()
                else:
                    await message.answer('Неправильный формат ввода')
            elif message.text == 'Отмена':
                await state.finish()
                ...
            else:
                await message.answer('Неправильный формат ввода')
                await state.finish()
                ...
        except IndexError:
            await state.finish()


@dp.message_handler(state=AdminStates.add_country)
async def add_country_state(message: types.Message, state: FSMContext):
    async with state.proxy():
        try:
            as_json = {str(x).split('=')[0].replace(' ', ''): str(x).split('=')[1] for x in message.text.split(',')}
        except IndexError:
            as_json = None
        if as_json:
            upd_country_dict = dict()
            columns_dict = database['country'].columns_dict
            for key, val in as_json.items():
                try:
                    if columns_dict[key]:
                        upd_country_dict.update({key: val if val != '' else None})
                except KeyError:
                    pass
            if len(upd_country_dict) == len(columns_dict):
                database['country'].upsert(upd_country_dict, pk='iso_code')
                await message.answer('Изменения сохранены')
                await state.finish()
            else:
                await message.answer('Неправильный формат ввода')
        elif message.text == 'Отмена':
            await state.finish()
            ...
        else:
            await message.answer('Неправильный формат ввода')
            await state.finish()
            ...


@dp.message_handler(state=AdminStates.delete_country)
async def delete_country_state(message: types.Message, state: FSMContext):
    async with state.proxy():
        try:
            as_json = {str(x).split('=')[0].replace(' ', ''): str(x).split('=')[1] for x in message.text.split(',')}
        except IndexError:
            as_json = None
        if as_json:
            upd_country_dict = dict()
            columns_dict = database['country'].columns_dict
            for key, val in as_json.items():
                try:
                    if columns_dict[key]:
                        upd_country_dict.update({key: val if val != '' else None})
                except KeyError:
                    pass
            if len(upd_country_dict) == 2:
                database['country'].delete_where('iso_code = :iso_code or name_eng = :name_eng',
                                                 {
                                                     'iso_code': upd_country_dict['iso_code'],
                                                     'name_eng': upd_country_dict['name_eng']
                                                 })
                await message.answer('Изменения сохранены')
                await state.finish()
            else:
                await message.answer('Неправильный формат ввода')
        elif message.text == 'Отмена':
            await state.finish()
            ...
        else:
            await message.answer('Неправильный формат ввода')
            await state.finish()
            ...
