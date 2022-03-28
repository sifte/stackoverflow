from typing import Any
from datetime import datetime
import os
import traceback

from discord.ext.commands import Bot as _Bot, Context, CommandNotFound, MissingRequiredArgument
from discord import Activity, ActivityType, AllowedMentions, Intents
from discord.utils import utcnow

from motor.motor_asyncio import AsyncIOMotorClient

from .constants import Config

EXTENSIONS: list = [
    f'cogs.{ext[:-3]}'
    for ext in os.listdir('./cogs')
    if ext.endswith('.py')
]

class StackBot(_Bot):
    """
    A subclassed discord.ext.commands.Bot class with some extra functionality.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            command_prefix='s!',
            strip_after_prefix=True,
            case_insensitive=True,
            intents=Intents.all(),
            allowed_mentions=AllowedMentions(everyone=False, users=True, roles=False),
            activity=Activity(type=ActivityType.watching, name='you answer questions | s!help'),
            **kwargs
            )
        self.start_time: datetime = utcnow() or None

    async def setup_hook(self) -> None:

        await self.load_extension('jishaku')

        for ext in EXTENSIONS:
            await self.load_extension(ext)

        
        if not hasattr(self, 'db'):
            self.db: AsyncIOMotorClient = AsyncIOMotorClient(Config.mongo_url)
        

    async def on_ready(self) -> None:
        message = f''' 
        Logged in as: {self.user}.
        --------------------------
        Guilds: {len(self.guilds):,}
        Users: {len(self.users):,}
        ID: {self.user.id}
        '''

        print(message)
    
    async def on_command_error(self, context: Context, exception: Exception) -> None:
        
        if isinstance(exception, CommandNotFound):
            return

        if isinstance(exception, MissingRequiredArgument):
            name = f"{context.command.qualified_name} {context.command.signature}"
            return await context.reply(name)


        await context.reply('An unknown error has occured. Sorry.')
        traceback.print_exc(type(exception), exception, exception.__traceback__)
