import discord
import os
import random
import json
import math
from operator import itemgetter
from datetime import datetime, timedelta
from discord.ext import commands
from discord import app_commands
from typing import Optional

description = '''Bot to track user's counts of S&P Coins as well as the current market value'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)

# initial values, although they are overwritten in on_ready if the relevant files exist

# a map of {user_id: number_of_coins_that_user_has}
user_coin_counts = {}

# turned off in prod - a map of {user_id: last_time_that_user_queried_value}
last_value_query_time_per_user = {}

# default value for the last market value. will be pulled from value.txt though
last_value = 1000

@bot.event
async def on_ready():
    global user_coin_counts
    global last_value
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    synced = await bot.tree.sync() #syncs the slash commands with discord

    print(f'Synced {len(synced)} commands')
    with open('user_coin_counts.txt', 'r') as f:
        user_coin_counts = json.loads(f.read())
    print('Loaded user_coin_counts')
    print(user_coin_counts)

    with open('value.txt', 'r') as f:
        last_value = float(f.read())
    print(f'Loaded last value: {last_value}')

    print('------')

# helper function to generate a new random value
# don't tell people about the proc or proc chance if they don't know already :)
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
    with open("value.txt", "w") as f:
        f.write(str(last_value))

def write_user_coin_counts_to_file():
    with open("user_coin_counts.txt", "w") as f:
        f.write(json.dumps(user_coin_counts))

def format_liquid(count):
    return '${:,.2f}'.format(count * last_value) + " USD"

"""
We use on_raw_reaction_add/remove instead of on_reaction_add/remove as the docs suggest that
there are cases on_reaction_add isn't called (when the message is not in the cache)
"""

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    print(payload.emoji.name)
    if (payload.emoji.name == os.environ['COIN_EMOJI_NAME']):

        if (payload.user_id == payload.message_author_id):
            return # we ignore coins added by the user that sent the message
        message_author_id = payload.message_author_id
        user_coin_counts[str(message_author_id)] = user_coin_counts.get(str(message_author_id), 0) + 1
        print(user_coin_counts[str(message_author_id)])
        write_user_coin_counts_to_file()

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if(payload.emoji.name == os.environ['COIN_EMOJI_NAME']):
        # only on_raw_reaction_add has the message property for some reason, so we have to manually fetch it here
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        message_author_id = message.author.id
        if (payload.user_id == message_author_id):
            return # we ignore coins added by the user that sent the message
        
        count = user_coin_counts.get(message_author_id, 1)
        user_coin_counts[str(message_author_id)] = count - 1 if count > 0 else 0
        write_user_coin_counts_to_file()

@bot.tree.command(
    name="wallet",
    description="Tells you how many S&P Coins you or another user have"
)
@app_commands.describe(member='The member you want to see the wallet of; defaults to the user who uses the command')
async def wallet(interaction, member: Optional[discord.Member] = None):
    member = member or interaction.user
    count = user_coin_counts.get(str(member.id), 0)
    coin_message = f'{member.mention} has {count} S&P Coins!' if count != 1 else f'{member.mention} has 1 S&P Coin!'
    message = coin_message + f' ({format_liquid(count)})'
    await interaction.response.send_message(message)

async def allowValueCheck(interaction):
    last_value_query_time_by_user = last_value_query_time_per_user.get(interaction.user.id)

    try:
        with open("slow_mode_hours.txt", "r") as f:
            slow_mode_hours = int(f.read())
    except:
        slow_mode_hours = 0
    
    if (slow_mode_hours is None or slow_mode_hours == 0):
        return True
    
    if last_value_query_time_by_user is not None:
        next_available_time = last_value_query_time_by_user + timedelta(hours=slow_mode_hours)
        if next_available_time > datetime.now():
            time_til_next = next_available_time - datetime.now()
            seconds_to_account_for = time_til_next.total_seconds()
            hours = math.floor(seconds_to_account_for / 3600)
            seconds_to_account_for = seconds_to_account_for - hours * 3600
            minutes = math.floor(seconds_to_account_for / 60)
            seconds_to_account_for = seconds_to_account_for - minutes * 60
            message = f"{hours} hours " if hours > 0 else ""
            message = message + f"{minutes} minutes " if minutes > 0 else ""
            message = message + f"{math.floor(seconds_to_account_for)} seconds"
            await interaction.response.send_message(f'Sorry, you can only check the market value once per {slow_mode_hours} hours. You can next check the market value in {message}.',
                                                    ephemeral=True)
            return False
    return True

# this is the syntax for saying "create a slash command with this name and description"
@bot.tree.command(
    name="value",
    description="Fetches the current market value of S&P Coin"
)
async def value(interaction):
    global last_value # this just means "if I use last_value in this function, it's the one defined globally, not a new one I just created in this scope"

    if not await allowValueCheck(interaction=interaction): # if slow_mode_hours is 0 this won't do anything
        return

    last_value_query_time_per_user[interaction.user.id] = datetime.now()

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

# helper function to get a user by ID
async def get_user_by_id(id):
    user = bot.get_user(id) # get_user is synchronous and based on the bot's cache
    if (user != None):
        return user
    
    return await bot.fetch_user(id) # this hits the discord API

'''Takes our dictionary of {user_id: coin_count} and converts it to {coin_count: [list_of_users]}'''
async def create_count_to_users_dict():
    count_to_users = {}
    for id,count in user_coin_counts.items():
        user = await get_user_by_id(id)
        if (count in count_to_users):
            count_to_users[count].append(user)
        else:
            count_to_users[count] = [user]

    return count_to_users

@bot.tree.command(
    name="ranking",
    description="Gets the top HODLers of S&P Coin"
)
@app_commands.describe(number='How many people to include, defaults to 5')
async def ranking(interaction, number:int=5):
    count_to_users = await create_count_to_users_dict()
    # get the top {number} amounts of coins
    rankings = list(reversed(sorted(count_to_users.keys())))[:number] #[:number] means take from index 0 number

    embed = discord.Embed(title=f'Top {len(rankings)} S&P Coin Bag Holders:')
    for count in rankings:
        users = count_to_users[count] # list of users with {count} coins

        users_string = users[0].mention # first (or only) user's @mention
        name = f'{count} ({format_liquid(count)})'
        if (len(users) > 1):
            name += " (tie)"
            for user in users[1:]:
                users_string += f', {user.mention}'
                
        embed.add_field(name=name, value=users_string, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(
    name="trade",
    description="Trade another user an amount of S&P Coin"
)
@app_commands.describe(member='The member you want to trade to')
async def trade(interaction, member: discord.Member, number: int):
    sending_user_id = str(interaction.user.id)
    sending_user_count = user_coin_counts.get(sending_user_id) or 0

    # do some edge case checking
    if interaction.user.id == member.id:
        await interaction.response.send_message("Nice try.", ephemeral=True)
        return
    if number < 0:
        await interaction.response.send_message("Be nice to the bot. -ada", ephemeral=True)
        return
    if number == 0:
        await interaction.response.send_message("Please trade more than 0 coins.", ephemeral=True)
        return
    if not (sending_user_count - number >= 0):
        await interaction.response.send_message(f"{interaction.user.mention} just tried to trade more coins than they had. Mock the brokey.")
        return

    # do the actual trade
    recipient_user_id = str(member.id)
    recipient_count = user_coin_counts.get(recipient_user_id) or 0

    sending_user_count = sending_user_count - number
    recipient_count = recipient_count + number

    user_coin_counts[sending_user_id] = sending_user_count
    user_coin_counts[recipient_user_id] = recipient_count

    write_user_coin_counts_to_file()

    embed = discord.Embed(title=f'A new trade has been made!',
                          description=f'''{interaction.user.mention} traded {member.mention} {number} <a:spcoinbot:1316612238290849822>
### New Wallets:''')
    embed.add_field(name=interaction.user.display_name, value=f"{sending_user_count} ({format_liquid(sending_user_count)})")
    embed.add_field(name=member.display_name, value=f"{recipient_count} ({format_liquid(recipient_count)})")

    await interaction.response.send_message(embed=embed)

# this actually starts the bot!
bot.run(os.environ['S_P_500_KEY'])
