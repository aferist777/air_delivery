import asyncio
from datetime import datetime

from aiogram import types

from config import USE_SCHEDULER, NOTIFY_USER_EVERY_HOURS, NOTIFY_USER
from core import logger, bot, scheduler
from data.database.database import fetchmany
from states.OrderStates import OrderStates


async def task_scheduler():
    if USE_SCHEDULER:
        logger.info(f'task_scheduler: RUN PENDING')
        JOBS = [
            scheduler.every(NOTIFY_USER_EVERY_HOURS).hours.do(notify_users, NOTIFY_USER)
        ]
        scheduler.jobs.clear()
        scheduler.jobs.extend(JOBS)
        jsoin_str = ",\n"
        logger.info(f'task_scheduler: current tasks:\n\n{jsoin_str.join(map(str, scheduler.jobs))}\n')
        while True:
            await scheduler.run_pending()
            await asyncio.sleep(1)


async def notify_users(custom_time: int):
    orders = await fetchmany('''SELECT * FROM bot."order" WHERE contractor_id is null AND state = $1''',
                             [OrderStates.order_accepted.state])
    if len(orders) > 0 and custom_time > 0:
        for order in orders:
            now = datetime.timestamp(datetime.now())
            delta = now - order['create_time']
            if delta >= custom_time * 60:
                customer_id = order['customer_id']
                state = order['state']
                if order['role'] == 'traveler':
                    await notify_traveler(customer_id, state)
                if order['role'] == 'sender':
                    await notify_sender(customer_id, state)


async def notify_traveler(customer_id: int, by_state: str):
    if by_state == OrderStates.order_accepted.state:
        my_travels = await fetchmany('''SELECT * FROM bot."order" WHERE customer_id = $1 AND role = 'traveler' AND state = $2
             ORDER BY departure_date_posix''', [customer_id, by_state])
        if len(my_travels) > 0:
            for mt in my_travels:
                filtered_parcels = await fetchmany('''SELECT count(*) FROM bot."order" WHERE customer_id != $1 AND role = 'sender' AND state = $2 AND departure_country = $3 AND arrival_country = $4
                     ORDER BY create_time''', [customer_id, by_state, mt['departure_country'], mt['arrival_country']])

                full_match = await fetchmany('''SELECT count(*) FROM bot."order" WHERE customer_id != $1 AND role = 'sender' AND state = $2 AND flight_route = $3
                     ORDER BY create_time''', [customer_id, by_state, mt['flight_route']])

                IK = types.InlineKeyboardMarkup(row_width=2)
                if len(full_match) > 0 or len(filtered_parcels) > 0:
                    full_match_text = """👋 В город, **куда Вы собираетесь лететь** появились посылки!

*Нажмите, на кнопку “Посылки", чтобы узнать подробнее*"""
                    IK.insert(types.InlineKeyboardButton('👀 Посылки',
                                                         callback_data=f"{customer_id}_get-nearby-customers"))
                    await bot.send_message(customer_id, full_match_text,
                                           parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK)


async def notify_sender(customer_id: int, by_state: str):
    filtered_parcels = tuple()
    full_match = tuple()
    if by_state == OrderStates.order_accepted.state:
        my_parcels = await fetchmany('''SELECT * FROM bot."order" WHERE customer_id = $1 AND role = 'sender' AND state = $2
             ORDER BY create_time''', [customer_id, by_state])
        if len(my_parcels) > 0:
            for mp in my_parcels:
                filtered_parcels = await fetchmany('''SELECT count(*) FROM bot."order" WHERE customer_id != $1 AND role = 'sender' AND state = $2 AND departure_country = $3 AND arrival_country = $4
                     ORDER BY departure_date_posix''', [customer_id, by_state, mp['departure_country'],
                                                        mp['arrival_country']])

                full_match = await fetchmany('''SELECT count(*) FROM bot."order" WHERE customer_id != $1 AND role = 'traveler' AND state = $2 AND flight_route = $3
                     ORDER BY create_time''', [customer_id, by_state, mp['flight_route']])

            IK = types.InlineKeyboardMarkup(row_width=2)
            if len(full_match) > 0:
                full_match_text = """*👋 В город, куда **Вы собираетесь отправить посылку**, появился путешественник.* 

*Нажмите, на кнопку “Путешественники"*"""
                IK.insert(types.InlineKeyboardButton('🗣 Путешественники',
                                                     callback_data=f"{customer_id}_get-nearby-contractors"))
                await bot.send_message(customer_id, full_match_text,
                                       parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK)
            if len(filtered_parcels) > 0 and not len(full_match) > 0:
                filtered_parcels_text = """"👋 В страну, **куда Вы собираетесь отправить посылку**, появился путешественник. 

🤔 Может у Вас там есть кто-то, кто сможет встретить посылку?

*Нажмите, на кнопку “Путешественники", чтобы узнать подробнее”*"""
                IK.insert(types.InlineKeyboardButton('🗣 Путешественники',
                                                     callback_data=f"{customer_id}_get-nearby-contractors_customer-has-orders_"))
                await bot.send_message(customer_id, filtered_parcels_text,
                                       parse_mode=types.ParseMode.MARKDOWN, reply_markup=IK)