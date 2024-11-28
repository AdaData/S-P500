# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands
import random

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
    print('------')

@bot.command()
async def count(ctx):
    await ctx.send(f'You have {kekws.get(ctx.author.id, 0)} somie coins!')

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """"""
    print(payload.emoji)
    if (payload.emoji.name == 'kekw'):
        message_author_id = payload.message_author_id
        kekws[message_author_id] = kekws.get(message_author_id, 0) + 1
        print(kekws)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """"""
    if(payload.emoji.name == 'kekw'):
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        message_author_id = message.author.id
        kekws[message_author_id] = kekws.get(message_author_id, 1) - 1
        print(kekws)

bot.run('key')
