import random
import string
import time
from contextlib import suppress
from datetime import datetime

from data.database.database import executeone, fetchmany
from data.database.db_api import fetchone_last_order_id, fetchmany_countries


def str_time_prop(start, end, time_format, prop):
    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))
    ptime = stime + prop * (etime - stime)
    return time.strftime(time_format, time.localtime(ptime)), ptime


def random_date(start, end, prop):
    return str_time_prop(start, end, '%d/%m/%Y', prop)


async def generate_random_orders(table_size: int):
    st = time.perf_counter()
    print('START gen_ord.generate_random_orders')
    upserted_count = 0
    last_row_order_id = await fetchone_last_order_id()
    stmnt = '''INSERT INTO bot.order VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)'''
    countries = await fetchmany_countries()
    if len(countries) > 0:
        for i in range(last_row_order_id + 1, table_size):
            with suppress(IndexError):
                departure_country = random.choice(countries)
                q_0 = await fetchmany('''SELECT * FROM bot.airport WHERE country_eng = $1''',
                                     [departure_country['name_eng']])
                departure_city = random.choice(q_0)

                arrival_country = random.choice(countries)
                q_1 = await fetchmany('''SELECT * FROM bot.airport WHERE country_eng = $1''', [arrival_country['name_eng']])
                arrival_city = random.choice(q_1)

                rnd_id = random.randint(100000000099, 999999999999)
                role = random.choice(['sender', 'traveler'])
                await executeone('''INSERT INTO bot.user(user_id, agree_with_rules, phone) VALUES ($1,$2,$3)''',
                                 [rnd_id, True, '+' + str(random.randint(10000000000, 99999999999))])

                print(f"gen_ord.generate_random_orders: upsert: {i}/{table_size}")
                upserted_count += 1
                date, posix_date = random_date("28/01/2022", "01/12/2030", random.random())
                values = [
                    i,
                    None,
                    rnd_id,
                    role,
                    'OrderStates:order_accepted',
                    date if role == 'traveler' else 'None',
                    posix_date if role == 'traveler' else 0.0,
                    departure_country['name_eng'],
                    departure_city['city_eng'],
                    departure_city['iata_code'],
                    arrival_country['name_eng'],
                    arrival_city['city_eng'],
                    arrival_city['iata_code'],
                    f"{departure_country['flag']}{departure_country['name_eng']}, {departure_city['city_eng']}|{departure_city['iata_code']}"
                    f" - {arrival_country['flag']}{arrival_country['name_eng']}, {arrival_city['city_eng']}|{arrival_city['iata_code']}",
                    f"{''.join(random.choice(string.ascii_letters + ' ') for _ in range(100))}",
                    datetime.timestamp(datetime.now())
                ]
                await executeone(stmnt, values)
    else:
        print('countries empty')
    end = time.perf_counter()
    print(f"END gen_ord.generate_random_orders: time: {round((end - st) / 60, 1)} min")
