from typing import Optional

from discord import ButtonStyle, ui
from discord.ext.commands import Context
from discord import Interaction

from motor.motor_asyncio import AsyncIOMotorCollection

class ConfirmView(ui.View):
    def __init__(self, ctx: Context):
        super().__init__()
        self.ctx = ctx
        self.value: Optional[bool] = None

    async def on_timeout(self) -> None:

        for item in self.children:
            item.disabled = True

        return await self.message.edit(content='You took too long. Goodbye!', view=self, embed=None)

    @ui.button(label='Confirm', style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: ui.Button) -> None:

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(content='Question submitted.', view=self)

        self.value = True
        self.stop()


    @ui.button(label='Cancel', style=ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: ui.Button) -> None:
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(content='Cancelled.', view=self)

        self.value = False
        self.stop()

class QuestionView(ui.View):
    def __init__(self, db: AsyncIOMotorCollection, question_id: int):
        super().__init__(timeout=60)
        self.db = db
        self.question_id = question_id

    async def on_timeout(self) -> None:

        for item in self.children:
            item.disabled = True

        return await self.message.edit(view=self)

    @ui.button(label='Upvote', style=ButtonStyle.green)
    async def upvote(self, interaction: Interaction, button: ui.Button) -> None:
        question = await self.db.find_one({'_id': self.question_id})

        if question is None:
            return await interaction.response.send_message('Question not found.')


        for dictionary in question['upvotes']:
            for item in dictionary.items():
                if item[1] == interaction.user.id:
                    return await interaction.response.send_message('You have already upvoted this question.', ephemeral=True)
        
        question['upvotes'].append({'user_id': interaction.user.id})

        await self.db.update_one({'_id': self.question_id}, {'$set': {'upvotes': question['upvotes']}})

        await interaction.response.send_message('Upvoted.', ephemeral=True)


    @ui.button(label='Downvote', style=ButtonStyle.red)
    async def downvote(self, interaction: Interaction, button: ui.Button) -> None:
        question = await self.db.find_one({'_id': self.question_id})

        if question is None:
            return await interaction.response.send_message('Question not found.')


        for dictionary in question['downvotes']:
            for item in dictionary.items():
                if item[1] == interaction.user.id:
                    return await interaction.response.send_message('You have already downvoted this question.', ephemeral=True)
        
        question['downvotes'].append({'user_id': interaction.user.id})

        await self.db.update_one({'_id': self.question_id}, {'$set': {'downvotes': question['downvotes']}})

        await interaction.response.send_message('Downvoted.', ephemeral=True)