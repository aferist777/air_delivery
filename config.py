import json
import os

ADMINS = ['']

DEMO_MODE = False

DEBUG_MODE = False
USE_REDIS = True
USE_SCHEDULER = True

NOTIFY_USER_EVERY_HOURS = 6  # запуск уведомлений для всех пользователей
NOTIFY_USER = 60  # параметр для проверки времени прошедшего с момента создания заказа

PATH_TO_SQL_SCRIPT = 'data/database/airbot.sql'
PATH_TO_LOG_FILE = 'log.log'

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 15,
    'pool_size': 100000,
    'prefix': 'my_fsm_key'
}

PG_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'airbot',
    'user': os.environ['PGADMIN'],
    'password': os.environ['PGADMINPASS'],
}

PG_CODEC = {
    'typename': 'json',
    'encoder': json.dumps,
    'decoder': json.loads,
    'schema': 'pg_catalog'
}

PG_DSN = f"postgresql://{PG_CONFIG['user']}:{PG_CONFIG['password']}" \
         f"@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"

MESSAGE_DELAY = 0.25

CONTRACTOR_ACTIVE_ORDERS_LIMIT = 1
CUSTOMER_ACTIVE_ORDERS_LIMIT = 5

NUMBER_OF_MATCHING_ADS = 27 if CUSTOMER_ACTIVE_ORDERS_LIMIT <= 2 else 18 * CUSTOMER_ACTIVE_ORDERS_LIMIT
ITEMS_PER_PAGE = 3

MIN_BIO_CHARS = 10
MAX_BIO_CHARS = 200

privacy_policy_LINK = '[Политика конфиденциальности](https://telegra.ph/Politika-konfidencialnosti-09-05-3)'
safety_regulations_LINK = '[Правила безопасности](https://telegra.ph/Pravila-bezopasnosti-08-20)'
baggage_rules_LINK = '[Правилами провозки багажа](https://b2b.aviasales.ru/help/airlines-airtickets/pravila-i-normy-provoza-bagazha)'
about_me_LINK = '[Как заполнить "О себе"](https://telegra.ph/Kak-zapolnit-O-sebe-08-22)'
group_chat_LINK = 'https://t.me/+E0b_-3VsvgIzYzdi'
group_chat_LINK_MD = 'https://t.me/+E0b\_-3VsvgIzYzdi'  # \
donation_service_LINK = 'https://www.donationalerts.com/c/samcali'
support_bot_LINK = '@airDeliverySupportBot'

base_countries = \
    {
        'RU': {'name_rus': 'Россия', 'name_eng': 'Russian Federation', 'flag': '🇷🇺'},
        'US': {'name_rus': 'США', 'name_eng': 'United States', 'flag': '🇺🇸'},
        'CA': {'name_rus': 'Канада', 'name_eng': 'Canada', 'flag': '🇨🇦'},
        'AE': {'name_rus': 'ОАЭ', 'name_eng': 'United Arab Emirates', 'flag': '🇦🇪'},
        'KZ': {'name_rus': 'Казахстан', 'name_eng': 'Kazakhstan', 'flag': '🇰🇿'},
        'BY': {'name_rus': 'Беларусь', 'name_eng': 'Belarus', 'flag': '🇧🇾'},
        'AM': {'name_rus': 'Армения', 'name_eng': 'Armenia', 'flag': '🇦🇲'},
        'GE': {'name_rus': 'Грузия', 'name_eng': 'Georgia', 'flag': '🇬🇪'},
        'MX': {'name_rus': 'Мексика', 'name_eng': 'Mexico', 'flag': '🇲🇽'},
        'TR': {'name_rus': 'Турция', 'name_eng': 'Turkey', 'flag': '🇹🇷'},
        'IN': {'name_rus': 'Индия', 'name_eng': 'India', 'flag': '🇮🇳'},
        'ID': {'name_rus': 'Индонезия', 'name_eng': 'Indonesia', 'flag': '🇮🇩'},
    }

base_commands = \
    [
        {'command': 'start', 'description': 'запуск бота'},
        {'command': 'help', 'description': 'помощь'},
    ]

admin_commands = \
    [
        {'command': 'admin', 'description': 'администратор'},
        {'command': 'get_logs', 'description': 'журнал событий'}
    ]

private_commands = \
    [
        {'command': 'set_sender_bio', 'description': 'обновить инф отправителя'},
        {'command': 'ser_traveler_bio', 'description': 'обновить инф путешественника'},
    ]

user_registration_TEXT = """✅ Чтобы сервис оставался безопасным местом пройдите простую регистрацию. Введите Ваши реальные имя и фамилию.

❗ Ваше имя должно совпадать с именем в удостоверении личности. Чтобы при встрече Вас не приняли за мошенника, а посылка попала в нужные руки.

🤔 Профили вызывающие подозрения, будут проходить дополнительную ручную проверку.

🖋 Введите Ваши имя и фамилию:"""

taking_flight_TEXT = """🗺 Здесь Вы можете *создать объявление* о Вашем путешествии, и готовы предложить Ваше свободное место в багаже.

📅 Выберите дату Вашего путешествия:"""

find_companion_TEXT = """🗺 Здесь Вы можете *создать объявление* о том, что ищете попутчика для своего отправления.

🛫Выберите страну и город, *откуда* Вам нужно отправить посылку:"""

customer_flight_route_comment_ITEM = """- размеры и вес Вашего отправления;
- район, где Вам удобно встретиться;
- цену, которую хотите предложить (имейте ввиду, что Вы платите не за саму перевозку, а за скорость перевозки).

*Ваш комментарий:*"""

contractor_flight_route_comment_ITEM = """- размеры и вес отправлений, который готовы взять;
- район, где Вам удобно встретиться;
- разную стоимость для разных размеров посылок. А если готовы бесплатно, то тоже укажите

*Ваш комментарий:*"""

important_info_BTN_TEXT = f"""*Дорогие пользователи, я хочу с Вами быть искренним и честным с самого начала.*

Я вижу, как русскоязычное комьюнити по всему миру, не смотря на многие разногласия, и не смотря на то, как это показывают в СМИ, остаётся очень дружным и сплоченным.

Я сам прохожу все сложности адаптации в США в одиночку. Так же даю советы и точно так же задаю вопросы во многих чатах. И я решил внести свою лепту в развитие русскоязычного комьюнити и создал бесплатного бота, который поможет Вам найти попутчиков для посылок, а путешествующим возможность отбить стоимость перелётов, *если возите за вознаграждение*. Знаю, что идея не новая и таких чатов пруд пруди. Но я постарался сделать *удобное место* для поиска попутчиков и посылок и *ради идеи адаптации человека к жизни в новых условиях*.

*Друзья, бот является НЕ коммерческим, и я не зарабатываю на Ваших отправлениях. О стоимости и безопасности посылок Вы заботитесь САМОСТОЯТЕЛЬНО. Почитать правила безопасности Вы сможете ниже по ссылке!*

*Вопросы по работе бота Вы можете задать в общем чате, а так же пообщаться с другими пользователями:*
{group_chat_LINK_MD}

*Чтобы Вы были предупреждены о мошенниках*, коих везде достаточно, я позаботился и написал несколько  правил, которые не позволят мошенникам завестись в наших рядах. *Не пренебрегайте ими*.

*Почитать их можно здесь:*
{safety_regulations_LINK}.

Если есть, что добавить к правилам, то напишите в чат по ссылке {group_chat_LINK_MD} с хэштегом #admin\_security

Сейчас может показаться, что бот выглядит, как что-то непонятное и неживое, но со временем объявлений станет больше, и ботом станет удобно пользоваться, поэтому прошу Вас, останьтесь и посмотрите 😉

Если наберем 10 000 пользователей, тогда я сделаю удобный сайт для Вас. Счетчик пользователей я добавил в главном меню! *Обновляется раз в 3 часа.*

И если Вы знаете людей, которые часто путешествуют, или которым было бы полезно и интересно узнать об этом боте, то посоветуйте им познакомиться. Это ускорит процесс набора определенной аудитории, чтобы попутчики и отправители находили друг друга вовремя и всегда.

*Спасибо, что сегодня Вы нашли меня! Всем мир <3*"""
