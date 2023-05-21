from aiogram.dispatcher.filters.state import StatesGroup, State


class ContractorStates(StatesGroup):
    set_departure_date = State()
    set_order_comment = State()
    set_cost_delivery = State()
