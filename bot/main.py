import asyncio

from ext.bot import StackBot
from ext.constants import Config

async def main() -> None:
    bot = StackBot()

    async with bot:
        await bot.start(Config.token)    

if __name__ == '__main__':
    asyncio.run(main())