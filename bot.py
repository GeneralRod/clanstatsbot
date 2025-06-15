import discord
from discord.ext import commands
import requests  
import os
from dotenv import load_dotenv

load_dotenv()  

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = "https://brawlhalla.solarauth.workers.dev/2515133"  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_clan_data():
    headers = {"Authorization": f"Bearer {API_KEY}"} 
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error collecting API: {response.status_code}")
        return None

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in')

@bot.command(name='clanstats')
async def clan_stats(ctx):
    clan_data = get_clan_data()
    if not clan_data:
        await ctx.send("Couldn't get the clan data")
        return

    sorted_players = sorted(clan_data['players'], key=lambda x: x.get('rating', 0) or 0, reverse=True)

    chunk_size = 1900
    chunks = []
    current_chunk = ""

    for i, player in enumerate(sorted_players, start=1):
        name = player.get('username', 'Unknown')
        if len(name) > 20:
            name = name[:17] + "..."

        rating = player.get('rating', 0) or 0
        peak_rating = player.get('peak_rating', 0) or 0
        wins = player.get('wins', 0) or 0
        games = player.get('games', 0) or 0

        line = (f"{i}. {name.ljust(20)} "
                f"Rating: {str(rating).rjust(5)}  "
                f"Peak: {str(peak_rating).rjust(5)}  "
                f"Wins: {str(wins).rjust(5)}  "
                f"Games: {str(games).rjust(5)}\n")

        if len(current_chunk) + len(line) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        await ctx.send(f"```{chunk}```")

bot.run(TOKEN)
