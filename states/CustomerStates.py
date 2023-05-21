from aiogram.dispatcher.filters.state import StatesGroup, State


class CustomerStates(StatesGroup):
    set_departure_date = State()
    set_cost_delivery = State()
    set_order_comment = State()
