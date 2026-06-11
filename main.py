import asyncio
import os
import discord
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import commands
from dbhandler import DBHandler
from dbhandler import POINTS_RESULT_PREDICTED, POINTS_WINNER_PREDICTED
from teams_dict import teams_dict
from votehandler import VoteHandler


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WC_CHANNEL_ID = int(os.getenv('WC_CHANNEL_ID'))

if DISCORD_TOKEN is None:
    raise ValueError("No DISCORD_TOKEN found in environment variables.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

db_handler = DBHandler()
vote_handler = VoteHandler()


@bot.event
async def on_ready():
    print(f'Bot has logged in as {bot.user}')
    # asyncio.create_task(notify_match_start())

@bot.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(colour = discord.Colour.green())
    embed.set_author(name='Player commands')
    embed.add_field(name='!help', value='Commands description', inline=False)
    embed.add_field(name='!voteinfo', value='Top scorer and country winner IDs', inline=False)
    embed.add_field(name='!schedule', value='Tournament timetable', inline=False)
    embed.add_field(name='!preds', value='Show your predictions', inline=False)
    embed.add_field(name='!lb', value='Display leaderboard', inline=False)
    embed.add_field(name='!getvotes', value='Get votes, ex. (!getvotes)', inline=False)
    embed.add_field(name='!voteteam [country_id]', value='Country winner bet, ex. (!voteteam 1)', inline=False)
    embed.add_field(name='!voteplayer [player_id]', value='Top scorer bet, ex. (!voteplayer 1)', inline=False)
    embed.add_field(name='!addbet [match_id] [bet]', value='Creates a new bet, ex. (!addbet 1 3-2)', inline=False)
    await ctx.channel.send(embed=embed)

    embed = discord.Embed(colour = discord.Colour.red())
    embed.set_author(name='Admin commands')
    embed.add_field(name='!topplayer [player_id]', value='Set top scorer, ex. (!topplayer 1)', inline=False)
    embed.add_field(name='!topteam [country_id]', value='Set country winner, ex. (!topteam 1)', inline=False)
    embed.add_field(name='!addmatch [match_id] [team1] [team2]', value='New match - for knockout stage, ex. (!addmatch 38 Polska Niemcy)', inline=False)
    embed.add_field(name='!addresult [match_id] [result]', value='Update match result, ex. (!addresult 3 2-2)', inline=False)
    await ctx.channel.send(embed=embed)


@bot.command(name='dump')
async def sendfiles(ctx):
    f1 = "./votes.json"
    f2 = "./bets.json"
    try:
        if os.path.exists(f1):
            await ctx.send("Here's the votes file you requested!", file=discord.File(f1))
        else:
            await ctx.send(f"File {f1} not found.")
    except Exception as e:
        await ctx.send(f"Failed to send votes file: {e}")
    
    try:
        if os.path.exists(f2):
            await ctx.send("Here's the bets file you requested!", file=discord.File(f2))
        else:
            await ctx.send(f"File {f2} not found.")
    except Exception as e:
        await ctx.send(f"Failed to send bets file: {e}")


@bot.command(name='voteteam')
async def bet_winner(ctx, country_id):
    user_name = str(ctx.author)
    message = vote_handler.bet_winner(country_id, user_name)
    await ctx.send(message)

@bot.command(name='voteplayer')
async def bet_player(ctx, player_id):
    user_name= str(ctx.author)
    message = vote_handler.bet_top_scorer(player_id, user_name)
    await ctx.send(message)

@bot.command(name='topteam')
async def add_country(ctx, country_id):
    message = vote_handler.add_winner(country_id)
    await ctx.send(message)

@bot.command(name='topplayer')
async def add_player(ctx, player_id):
    message = vote_handler.add_top_scorer(player_id)
    await ctx.send(message)

@bot.command(name='getvotes')
async def get_votes(ctx):
    countries, players = vote_handler.get_votes()
    context = "Votes for top scorer: \n"
    for ind, player in players.items():
        context += str(ind) + ": " + player + "\n" 
    await ctx.send(context)
    context = "Votes for cup winner: \n"
    print(countries)
    print(players)
    for ind, country in countries.items():
        context += str(ind) + " :" + country + ": \n" 
    await ctx.send(context)

@bot.command(name='voteinfo')
async def vote_info(ctx):
    message = vote_handler.get_vote_info()
    context = "Vote for top scorer: \n"
    for ind, data in enumerate(message['players'], start=1):
        context += str(ind) + ". " + data[0] + " :" +  teams_dict[data[1]] + ": \n" 
    await ctx.send(context)    
    context = "Vote for cup winner: \n"
    for ind, country in enumerate(message['countries'], start=1):
        context += str(ind) + ". :" + country + ": \n" 
    await ctx.send(context)

@bot.command(name='preds')
async def my_predictions(ctx):
    user_name = str(ctx.author)
    predictions = db_handler.get_users_predictions(user_name)
    context = "GROUP STAGE\n"
    for prediction in predictions[:36]: # group stage
        context += str(prediction["match_id"]) + ". " + prediction["teams"] + "    " + prediction["result"] \
            + "    Bet: " + prediction["bet"] + "\n"
    await ctx.send(context)
    context = ""
    for prediction in predictions[36:72]: # group stage
        context += str(prediction["match_id"]) + ". " + prediction["teams"] + "    " + prediction["result"] \
            + "    Bet: " + prediction["bet"] + "\n"
    await ctx.send(context)
    context = "KNOCKOUT STAGE\n"
    for prediction in predictions[72:]: # knockout stage
        context += str(prediction["match_id"]) + ". " + prediction["teams"] + "    " + prediction["result"] \
            + "    Bet: " + prediction["bet"] + "\n"
    await ctx.send(context)


async def notify_match_start():
    schedule = db_handler.get_schedule()
    while True:
        for match in schedule:
            match_time = match['datetime']
            notification_time = match_time - timedelta(minutes=1)
            now = datetime.now() + timedelta(hours=2)
            if now >= notification_time and now < match_time:
                print(now)
                channel = bot.get_channel(WC_CHANNEL_ID)
                if channel:
                    bets = db_handler.get_bets_for_match(match['match_id'])
                    context = str(match_time) + "\n" + bets['teams'] + "\n"
                    for bet in bets['bets']:
                        context += bet['user'] + ": " + bet['proposed_result'] + "\n"
                    await channel.send(context)
        await asyncio.sleep(60)


@bot.command(name='lb')
async def leaderboard(ctx):
    leaderboard = db_handler.get_leaderboard()
    context = ""
    for rank, (user, score) in enumerate(leaderboard, start=1):
        if rank == 1:
            context += ':first_place: '
        if rank == 2:
            context += ':second_place: '
        if rank == 3:
            context += ':third_place: '
        if rank not in [1,2,3]:
            context += str(rank) +  ". "
        context += user + "    " + str(score) + "\n"
    if leaderboard:
        await ctx.send(context)
    else:
        await ctx.send("Tournament has not yet started")


@bot.command(name='addbet')
async def addbet(ctx, match_id, result):
    if bool(re.match(r'^\d+-\d+$', result)) == False:
        await ctx.send("Incorrect result -> accepted '1-1', '2-0' etc.")
        return
    user_name = str(ctx.author)
    message = db_handler.add_bet(match_id, user_name, result)
    await ctx.send(message)


@bot.command(name='addmatch')
async def addmatch(ctx, match_id, team1, team2):
    message = db_handler.add_match(match_id, team1, team2)
    await ctx.send(message)


@bot.command(name='schedule')
async def schedule(ctx):
    schedule = db_handler.get_schedule()
    context = "GROUP STAGE\n"
    for match in schedule[:36]: # group stage
        context += str(match["match_id"]) + ". " + match["teams"] + "    " + str(match["datetime"]) + "\n"
    await ctx.send(context)
    context = ""
    for match in schedule[36:72]: # group stage
        context += str(match["match_id"]) + ". " + match["teams"] + "    " + str(match["datetime"]) + "\n"
    await ctx.send(context)
    context = "KNOCKOUT STAGE\n"
    for match in schedule[72:88]: # knockout stage
        context += str(match["match_id"]) + ". " + match["teams"] + "    " + str(match["datetime"]) + "\n"
    await ctx.send(context)
    context = ""
    for match in schedule[88:]: # knockout stage
        context += str(match["match_id"]) + ". " + match["teams"] + "    " + str(match["datetime"]) + "\n"
    await ctx.send(context)


@bot.command(name='addresult')
async def addresult(ctx, match_id, result):
    if bool(re.match(r'^\d+-\d+$', result)) == False:
        await ctx.send("Incorrect result -> accepted '1-1', '2-0' etc.")
        return
    message = db_handler.add_result(match_id, result)
    await ctx.send(message)
    match = db_handler.get_bets_for_match(int(match_id))
    context = str(match['teams']) + ": " + str(result) + "\n" + "Points scored:\n"
    for bet in match['bets']:
        if db_handler.is_result_predicted(bet['proposed_result'], result):
            context += bet['user'] + ": " + str(POINTS_RESULT_PREDICTED) + "\n"
        elif db_handler.is_winner_predicted(bet['proposed_result'], result):
            context += bet['user'] + ": " + str(POINTS_WINNER_PREDICTED) + "\n"
        else:
            context += bet['user'] + ": 0\n"

    channel = bot.get_channel(WC_CHANNEL_ID)
    if channel:
        await channel.send(context)


@bot.event
async def on_message(message):
    print(f'Received message in channel: {message.channel} from {message.author}')

    # Check if the message is from a bot
    if message.author.bot:
        return

    # Handle messages in the 'worldcup' channel in a server
    if isinstance(message.channel, discord.TextChannel):
        if message.channel.name == 'worldcup':
            if message.content == 'hello':
                await message.channel.send('Hello \n Type "!help" to see available commands')
    
    # Handle direct messages
    elif isinstance(message.channel, discord.DMChannel):
        if message.content == 'hello':
            await message.channel.send('Hello! This is a DM.')

    await bot.process_commands(message)


bot.run(DISCORD_TOKEN)
