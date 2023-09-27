from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Restart the bot"),
            types.BotCommand("help", "Get instructions"),
            types.BotCommand("lane_info", "Get landmark status"),
            types.BotCommand("all_trl_info", "Get all trailers' locations"),
            types.BotCommand("trailer_loc", "Get one trailer's location"),
            types.BotCommand("lanes_update", "Get all landmark status"),
            types.BotCommand("distance", "Measure a distance between two addresses"),
            types.BotCommand("time_in", "For getting current local time for given location"),
            types.BotCommand("time_for", "For getting current local time for driver's location")
        ]
    )
