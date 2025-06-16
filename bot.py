import subprocess
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
import asyncio
import json
import logging
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = os.getenv("API_KEY")  # This should be the full URL to your JSON API

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def get_clan_data():
    if not API_URL:
        print("API_URL is not set in .env")
        return None
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            # Check if it's a list or dict
            if isinstance(data, list):
                return {"players": data}
            elif isinstance(data, dict):
                return data
            else:
                print("Unexpected data format from API")
                return None
        else:
            print(f"Error fetching API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception during API call: {e}")
        return None


def write_leaderboard_json(current_data, previous_data):
    # Debug prints
    print("Current data:", current_data)
    print("Previous data:", previous_data)
    
    # Ensure we always have a list of players
    current_players = current_data if isinstance(current_data, list) else current_data.get('players', [])
    previous_players = previous_data if isinstance(previous_data, list) else previous_data.get('players', [])
    
    print("Current players:", current_players)
    print("Previous players:", previous_players)
    
    # Sort current players by rating
    current_players = sorted(current_players, key=lambda x: x.get('rating', 0), reverse=True)
    
    leaderboard_list = []
    for player in current_players:
        # Debug print for each player
        print(f"\nProcessing player: {player.get('username')}")
        print(f"Current rating: {player.get('rating')}")
        
        # Find previous week data for this player
        current_username = player.get('username', '')
        prev_player = next((p for p in previous_players if p.get('name') == current_username), None)
        
        if prev_player:
            print(f"Found previous data: {prev_player}")
            print(f"Previous rating: {prev_player.get('rating')}")
        
        # Calculate rating difference
        current_rating = player.get('rating', 0)
        prev_rating = prev_player.get('rating', 0) if prev_player else current_rating
        rating_diff = current_rating - prev_rating
        
        print(f"Calculated rating diff: {rating_diff}")

        leaderboard_list.append({
            "name": current_username,
            "rating": current_rating,
            "rating_diff": rating_diff,
            "peak": player.get('peak_rating', 0),
            "wins": player.get('wins', 0),
            "games": player.get('games', 0),
        })

    path = os.path.join("puppeteer-leaderboard", "data", "week23.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(leaderboard_list, f, ensure_ascii=False, indent=2)
    
    print("\nFinal leaderboard list:", leaderboard_list)


@bot.command(name="leaderboard")
async def leaderboard(ctx):
    try:
        # Get current week number
        current_date = datetime.now()
        current_week = current_date.isocalendar()[1]
        previous_week = current_week - 1
        
        current_data = get_clan_data()
        if not current_data:
            await ctx.send("Could not fetch current clan data.")
            return

        print("Current data from API:", current_data)

        # Load previous week's data
        previous_data = []
        prev_path = os.path.join("puppeteer-leaderboard", "data", f"week{previous_week}.json")
        if os.path.exists(prev_path):
            with open(prev_path, "r", encoding="utf-8") as f:
                previous_data = json.load(f)
                print(f"Loaded previous data from week{previous_week}.json:", previous_data)

        # Write current data to JSON
        current_path = os.path.join("puppeteer-leaderboard", "data", f"week{current_week}.json")
        write_leaderboard_json(current_data, previous_data)

        # Run Puppeteer script
        render_path = os.path.join("puppeteer-leaderboard", "src", "render.js")
        subprocess.run(["node", render_path], check=True)

        # Send PNG
        img_path = os.path.join("puppeteer-leaderboard", "output", "leaderboard.png")
        if not os.path.exists(img_path):
            await ctx.send("Could not find the generated image.")
            return

        file = discord.File(img_path, filename="leaderboard.png")
        await ctx.send("Here is the updated leaderboard:", file=file)

        # If it's Sunday, save current data as base for next week
        if current_date.weekday() == 6:  # 6 is Sunday
            next_week = current_week + 1
            next_week_path = os.path.join("puppeteer-leaderboard", "data", f"week{next_week}.json")
            with open(next_week_path, "w", encoding="utf-8") as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            print(f"Saved current data as week{next_week}.json for next week's comparison")

    except subprocess.CalledProcessError:
        await ctx.send("Error generating image via render.js.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print("Error details:", str(e))


@bot.command(name="clanstats")
async def clan_stats(ctx):
    clan_data = get_clan_data()
    if not clan_data:
        await ctx.send("Could not fetch clan data.")
        return

    players = clan_data.get("players", [])
    sorted_players = sorted(
        [p for p in players if isinstance(p.get("rating", 0), (int, float))],
        key=lambda x: x["rating"],
        reverse=True
    )

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


@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    try:
        # Load cogs
        await bot.load_extension('moderation')
        await bot.load_extension('reactions')
        
        # Sync commands only once
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash commands synced")
    except Exception as e:
        print(f"❌ Error loading/syncing commands: {e}")


if __name__ == "__main__":
    bot.run(TOKEN)
