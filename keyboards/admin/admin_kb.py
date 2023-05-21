from aiogram import types

from core import bot
from data.database.db_api import fetchmany_countries


async def admin_panel_message_IK(user_id: int):
    IK = types.InlineKeyboardMarkup() \
        .add(types.InlineKeyboardButton('Управление странами', callback_data="countries-management"))
    await bot.send_message(user_id, 'Админ панель', reply_markup=IK)


async def countries_management_message_IK(user_id: int):
    IK = types.InlineKeyboardMarkup(row_width=2)
    _countries = await fetchmany_countries()
    if len(_countries) > 0:
        for country in _countries:
            callback_data = f"admin_update-country_{country['flag']}_{country['name_rus']}_{country['name_eng']}_{country['iso_code']}"
            country_text = f"{country['name_rus'] if country['name_rus'] else country['name_eng']} {country['flag']}"
            IK.insert(types.InlineKeyboardButton(country_text, callback_data=callback_data))
        IK.row(types.InlineKeyboardButton('add', callback_data=f"admin_add-country"),
               types.InlineKeyboardButton('del', callback_data=f"admin_delete-country"))
        await bot.send_message(user_id, "Здесь вы можете редактировать список *стран*",
                               parse_mode=types.ParseMode.MARKDOWN_V2,
                               reply_markup=IK)
    else:
        await bot.send_message(user_id, f"Список стран отсутствует в базе данных", reply_markup=IK)
