from loader import db, dp


async def monday_mileage():
    message = """<b>
🚚🌤MILEAGE MONDAY🌤🚚

❗️❗️GOOD MORNING TEAM ❗️❗️
🙏🏼DON'T FORGET TO SEND YOUR 🙏🏼
🚚 MONDAY MILEAGE REPORT 🚚
💥💥 NO LATER THAN 12PM!!! 💥💥

THANK YOU! 🙏 DRIVE SAFE! ✅</b>"""

    sql = """
    SELECT t.chat_id, t.truck_id FROM trucks t
    INNER JOIN drivers d ON t.chat_id = d.chat_id
    WHERE t.in_ownership = 0 AND d.is_active = 1;
    """

    chats = await db.execute(sql, fetchall=True)

    for chat in chats:
        await dp.bot.send_message(chat[0], message)
