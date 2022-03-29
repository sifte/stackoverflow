from time import perf_counter
from typing import Any

from discord.ext.commands import Context

from motor.motor_asyncio import AsyncIOMotorCollection

PAYLOAD: dict[str, Any] = {
    '_id': 999,
    'content': 'test'
}


async def get_latency(ctx: Context) -> dict[str, str]:
    """
    Get the bot's latency and database latency.

    Parameters
    ----------
    ctx : Context
        The context.
    """

    now = perf_counter()

    collection = ctx.bot.db['test']['TESTS']

    if await collection.find_one({'_id': PAYLOAD['_id']}) is None:
        await collection.insert_one(PAYLOAD)

    else:
        await collection.find_one({'_id': PAYLOAD['_id']})

    bot_latency = f'{round(ctx.bot.latency * 1000)}ms'
    database_latency = f'{round(perf_counter() - now)}ms'
    
    data: dict[str, str] = {
        'bot': bot_latency,
        'database': database_latency
    }
    
    return data