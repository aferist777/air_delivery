from aiogram.dispatcher.filters.state import StatesGroup, State


class AdminStates(StatesGroup):
    update_country = State()
    add_country = State()
    delete_country = State()
