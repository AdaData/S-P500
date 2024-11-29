# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
import os
import random
import json
from operator import itemgetter
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

user_coin_counts = {}

last_value = 1000

@bot.event
async def on_ready():
    global user_coin_counts
    global last_value
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    synced = await bot.tree.sync()
    print(f'Synced {len(synced)} commands')
    f = open('user_coin_counts.txt', 'r')
    user_coin_counts = json.loads(f.read())
    f.close()
    print('Loaded user_coin_counts')
    print(user_coin_counts)
    f = open('value.txt', 'r')
    last_value = float(f.read())
    print(f'Loaded last value: {last_value}')
    f.close()
    print('------')

@bot.tree.command(
    name="wallet",
    description="Tells you how many S&P Coins you have"
)
@app_commands.describe(member='The member you want to see the wallet of; defaults to the user who uses the command')
async def wallet(interaction, member: Optional[discord.Member] = None):
    member = member or interaction.user
    count = user_coin_counts.get(str(member.id), 0) # since we save these to JSON, they need to be stringifed
    coin_message = f'{member.mention} has {count} S&P Coins!' if count != 1 else f'{member.mention} has 1 S&P Coin!'
    formatted_liquid = '${:,.2f}'.format(count * last_value)
    message = coin_message + f' ({formatted_liquid} USD)'
    await interaction.response.send_message(message)

def get_new_value():
    procced = random.randint(0, 100) == 1
    if (not procced):
        factor = random.randint(1, 5) * .1
        botRange = int(last_value - (last_value * factor))
        topRange = int(last_value + (last_value * factor))
        dollars = random.randrange(botRange, topRange)
    else:
        dollars = random.randrange(0, 100000)
    cents = random.randrange(0, 99)
    value = dollars + (cents * .01)
    formatted_value = '${:,.2f}'.format(value)
    return {'value': value, 'formatted_value': formatted_value, 'procced': procced}

def get_perc_diff(value, last_value):
    return ((value - last_value) / last_value) * 100

def get_emoji_string(perc_diff):
    emoji = ':chart_with_upwards_trend:' if perc_diff > 0 else ':chart_with_downwards_trend:'
    emoji_string = emoji
    if (abs(perc_diff) > 15):
        emoji_string += emoji
    if (abs(perc_diff)) > 30:
        emoji_string += emoji
    return emoji_string

def write_value_to_file():
    f = open("value.txt", "w")
    f.write(str(last_value))
    f.close()

@bot.tree.command(
    name="value",
    description="Fetches the current market value of S&P Coin"
)
async def value(interaction):
    global last_value
    value, formatted_value, procced = itemgetter('value', 'formatted_value', 'procced')(get_new_value())
    perc_diff = get_perc_diff(value, last_value)
    emoji_string = get_emoji_string(perc_diff)

    message = 'MARKET FLUCTUATIONS! ' if procced else ''
    message += f'S&P Coin is currently trading at {emoji_string} U.S. {formatted_value}.'

    if (perc_diff < -30):
        message += " BUY BUY BUY!!!"
    elif (perc_diff > 30):
        message += " HODL! :gem: Diamond Hands :gem:"

    last_value = value
    write_value_to_file()

    await interaction.response.send_message(message)

def write_user_coin_counts_to_file():
    f = open("user_coin_counts.txt", "w")
    f.write(json.dumps(user_coin_counts))
    f.close()

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """"""
    if (payload.emoji.name == os.environ['COIN_EMOJI_NAME']):
        if (payload.user_id == payload.message_author_id):
            print('Ignoring coin added by the same user')
            return
        message_author_id = payload.message_author_id
        user_coin_counts[str(message_author_id)] = user_coin_counts.get(str(message_author_id), 0) + 1
        write_user_coin_counts_to_file()

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """"""
    if(payload.emoji.name == os.environ['COIN_EMOJI_NAME']):
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        message_author_id = message.author.id
        if (payload.user_id == message_author_id):
            print('Ignoring coin removed by the same user')
            return
        count = user_coin_counts.get(message_author_id, 1)
        user_coin_counts[str(message_author_id)] = count - 1 if count > 0 else 0
        write_user_coin_counts_to_file()

bot.run(os.environ['S_P_500_KEY'])
