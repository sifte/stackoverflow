from asyncio import TimeoutError

from discord import Color, Embed, Message
from discord.ext.commands import Cog, command, Context

from motor.motor_asyncio import AsyncIOMotorCollection

from ext.bot import StackBot
from ext.views import ConfirmView, QuestionView
from discord.utils import utcnow

TIMEOUT = 120
CHAR_LIMIT = 1501

class Meta(Cog):
    """
    The main category.
    """

    def __init__(self, bot: StackBot) -> None:
        self.bot = bot

    @property
    def db(self) -> AsyncIOMotorCollection:
        return self.bot.db['TESTING']['1'] # change to ['stackoverflow']['meta']

    @property
    def user_db(self) -> AsyncIOMotorCollection:
        return self.bot.db['TESTING']['user'] # change to ['stackoverflow']['users']

    async def ensure_user_exists(self, user_id: int) -> None:
        user = await self.user_db.find_one({'_id': user_id})

        if user is None:

            payload = {
                '_id': user_id,
                'questions_asked': [], # array of question ids
                'questions_answered': [], # array of question ids
            }
            await self.user_db.insert_one(payload)
            return

        else:
            return user

    async def post_question(self, user_id: int, data: dict) -> None:

        user = await self.ensure_user_exists(user_id)
        question_id = len(await self.db.find().to_list(100000)) + 1

        payload = {
            '_id': question_id,
            'user_id': user_id,
            'title': data['title'],
            'body': data['body'],
            'tags': data['tags'],
            'upvotes': [], 
            'downvotes': [],
            'answers': [],
            'views': 0,
            'date': int(utcnow().timestamp()),
        }

        await self.db.insert_one(payload)

        user['questions_asked'].append(question_id)
        await self.user_db.update_one({'_id': user_id}, {'$set': {'questions_asked': user['questions_asked']}})

        return

    async def prepare_message(self, ctx: Context, data: dict) -> Embed:
        embed = Embed(
            title=data['title'],
            description=data['body'],
            color=Color.dark_gold()
            )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        return embed

    @command(name='ask')
    async def ask(self, ctx: Context) -> None:
        
        def check(message: Message) -> bool:
            return message.author == ctx.author and message.channel == ctx.channel

        await ctx.send(f'Hello {ctx.author.mention}. What would you like the title of the question to be?')

        try:
            title = await self.bot.wait_for('message', check=check, timeout=TIMEOUT)
        except TimeoutError:
            return await ctx.send('You took too long to respond. Goodbye!')

        else:

            if len(title.content) >= CHAR_LIMIT:
                return await ctx.reply('The title of the question is too long. The maximum is 1500 characters.')

            await ctx.send(f'Great! What would you like the body of the question to be?')

        try:
            body = await self.bot.wait_for('message', check=check, timeout=TIMEOUT)
        except TimeoutError:
            return await ctx.send('You took too long to respond. Goodbye!')

        else:
            if len(title.content) >= CHAR_LIMIT:
                return await ctx.reply('The body of the question is too long. The maximum is 1500 characters.')

            await ctx.send(f'Great! What would you like the questions tags to be? (separated by commas e.g. python, javascript) If you do not want to add any tags, just type `none`.')

        try:
            tags = await self.bot.wait_for('message', check=check, timeout=TIMEOUT)
        except TimeoutError:
            return await ctx.send('You took too long to respond. Goodbye!')

        else:
            if len(tags.content.split(',')) == 0 or tags.content.lower() == 'none':
                tags = []

        view = ConfirmView(ctx)
        embed = await self.prepare_message(
            ctx, {
                'title': title.content,
                'body': body.content,
                'tags': tags.content.split(',')
                }
            )

        view.message = await ctx.reply(content='Are you sure you want to post this question?', embed=embed, view=view)

        await view.wait()

        if view.value is None:
            return await view.on_timeout()

        if view.value:
            data = {
                'title': title.content,
                'body': body.content,
                'tags': tags.content.split(',')
                }


            return await self.post_question(ctx.author.id, data)
        
        else:
            return

    async def prepare_question(self, question: dict) -> Embed:

        user = self.bot.get_user(question['user_id']) or await self.bot.get_user(question['user_id'])

        embed = Embed(
            title=question['title'],
            description=question['body'],
            color=Color.dark_gold()
            )

        timestamp = f"<t:{question['date']}>"

        if bool(question['tags']) is True:
            embed.add_field(name='Tags', value=', '.join(question['tags']))

        embed.add_field(name='Upvotes', value=len(question['upvotes']))
        embed.add_field(name='Downvotes', value=len(question['downvotes']))
        embed.add_field(name='Posted at', value=timestamp)
        embed.add_field(name='Views', value=question['views']) # increment on view
        embed.add_field(name='Answers', value=len(question['answers']))
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_footer(text=f'Question asked by {user}.')

        await self.db.update_one({'_id': question['_id']}, {'$inc': {'views': 1}})

        return embed


    @command(name='question') 
    async def question(self, ctx: Context, question_id: int) -> None:

        question = await self.db.find_one({'_id': question_id})

        if question is None:
            return await ctx.send('Question not found.')


        view = QuestionView(self.db, question_id)
        embed = await self.prepare_question(question)

        

        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot: StackBot) -> None:
    await bot.add_cog(Meta(bot))