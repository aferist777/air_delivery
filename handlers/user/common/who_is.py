from data.database.database import fetchone


async def is_in_database(user_id: int, checkin_contractor_table=False, checkin_customer_table=False):
    """
    call func:
        correct use: is_in_database(user_id, True, True, True)\n
        correct use: is_in_database(user_id, False, True, True)\n
    :return: {'checkin_user_table': bool, 'checkin_contractor_table': bool, 'checkin_customer_table': bool}
    """
    query_contractor_table = None
    query_customer_table = None
    query_contractor_orders_table = None
    query_customer_orders_table = None

    query_user_table = await fetchone("SELECT user_id FROM bot.user WHERE user_id = $1", [user_id])

    if checkin_contractor_table:
        query_contractor_table = await fetchone("SELECT user_id FROM bot.contractor WHERE user_id = $1", [user_id])

        if not query_contractor_table and query_user_table:
            query_contractor_orders_table = await fetchone(
                """SELECT id FROM bot.order WHERE customer_id = $1 and role = 'traveler'""", [user_id])
    if checkin_customer_table:
        query_customer_table = await fetchone("SELECT user_id FROM bot.customer WHERE user_id = $1 ", [user_id])

        if not query_customer_table and query_user_table:
            query_customer_orders_table = await fetchone(
                """SELECT id FROM bot.order WHERE customer_id = $1 and role = 'sender'""", [user_id])
    result_json = {
        'checkin_user_table': True if query_user_table else False,
        'checkin_contractor_table': True if query_contractor_table or query_contractor_orders_table else False,
        'checkin_customer_table': True if query_customer_table or query_customer_orders_table else False
    }
    return result_json
