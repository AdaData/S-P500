# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
import os
from discord.ext import commands
from discord import app_commands
from typing import Optional

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)

kekws = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    synced = await bot.tree.sync()
    print(f'Synced {len(synced)} commands')
    print('------')

@bot.tree.command(
    name="wallet",
    description="Tells you how many S&P Coins you have"
)
@app_commands.describe(member='The member you want to see the wallet of; defaults to the user who uses the command')
async def wallet(interaction, member: Optional[discord.Member] = None):
    member = member or interaction.user
    count = kekws.get(member.id, 0)
    await interaction.response.send_message(f'{member.mention} has {count} S&P Coins!' if count != 1 else f'{member.mention} has 1 S&P Coin!')

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """"""
    if (payload.emoji.name == 'kekw'):
        if (payload.user_id == payload.message_author_id):
            print('Ignoring coin added by the same user')
            return
        message_author_id = payload.message_author_id
        kekws[message_author_id] = kekws.get(message_author_id, 0) + 1

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """"""
    if(payload.emoji.name == 'kekw'):
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        message_author_id = message.author.id
        if (payload.user_id == message_author_id):
            print('Ignoring coin removed by the same user')
            return
        count = kekws.get(message_author_id, 1)
        kekws[message_author_id] = count - 1 if count > 0 else 0

bot.run(os.environ['S_P_500_KEY'])
