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


def write_leaderboard_json(current_data, previous_data, current_week):
    # Debug prints
    print("\n=== DEBUG: Starting write_leaderboard_json ===")
    print("Current week:", current_week)
    print("Current data structure:", type(current_data))
    print("Previous data structure:", type(previous_data))
    
    # Ensure we always have a list of players
    current_players = current_data if isinstance(current_data, list) else current_data.get('players', [])
    previous_players = previous_data if isinstance(previous_data, list) else previous_data.get('players', [])
    
    print("\nCurrent players count:", len(current_players))
    print("Previous players count:", len(previous_players))
    
    # Sort current players by rating
    current_players = sorted(current_players, key=lambda x: x.get('rating', 0), reverse=True)
    
    # Create a lookup dictionary for current players by name (for backfilling user IDs)
    current_name_lookup = {}
    for player in current_players:
        name = player.get('name', player.get('username', ''))
        current_name_lookup[name.lower()] = player
        # Also store simplified name (remove prefixes like "LFT I ")
        simplified_name = ' '.join(name.split()[1:]) if name.startswith('LFT I ') else name
        current_name_lookup[simplified_name.lower()] = player
    
    # Create a lookup dictionary for previous week's data
    prev_week_lookup = {}
    for player in previous_players:
        # Try to get user_id, fall back to name if not available
        player_id = player.get('user_id')
        if player_id:
            prev_week_lookup[player_id] = player
        else:
            # If no user_id, try to find it in current data
            name = player.get('name', '')
            simplified_name = ' '.join(name.split()[1:]) if name.startswith('LFT I ') else name
            
            # Try to find matching player in current data
            matching_player = current_name_lookup.get(name.lower()) or current_name_lookup.get(simplified_name.lower())
            if matching_player:
                player['user_id'] = matching_player.get('user_id')
                print(f"Backfilled user_id for {name}: {player['user_id']}")
                prev_week_lookup[player['user_id']] = player
            else:
                # If still no match, use name as fallback
                prev_week_lookup[name] = player
    
    leaderboard_list = []
    for player in current_players:
        # Debug print for each player
        print(f"\n=== Processing player ===")
        print(f"Name: {player.get('name', player.get('username', 'Unknown'))}")
        print(f"User ID: {player.get('user_id')}")
        print(f"Current rating: {player.get('rating')}")
        
        # Find previous week data for this player
        current_user_id = player.get('user_id')
        current_name = player.get('name', player.get('username', ''))
        
        # Try to find previous data by user_id first, then fall back to name
        prev_player = None
        if current_user_id and current_user_id in prev_week_lookup:
            prev_player = prev_week_lookup[current_user_id]
            print(f"Found match by user_id: {current_user_id}")
        elif current_name in prev_week_lookup:
            prev_player = prev_week_lookup[current_name]
            print(f"Found match by name: {current_name}")
        
        if prev_player:
            print(f"Found previous data:")
            print(f"  Name: {prev_player.get('name', prev_player.get('username', 'Unknown'))}")
            print(f"  User ID: {prev_player.get('user_id')}")
            print(f"  Previous rating: {prev_player.get('rating')}")
        else:
            print("No previous data found for this player")
        
        # Calculate rating difference
        current_rating = player.get('rating', 0)
        prev_rating = prev_player.get('rating', 0) if prev_player else current_rating
        rating_diff = current_rating - prev_rating
        
        print(f"Rating calculation:")
        print(f"  Current rating: {current_rating}")
        print(f"  Previous rating: {prev_rating}")
        print(f"  Calculated diff: {rating_diff}")

        # Always include user_id in the saved data
        leaderboard_list.append({
            "name": player.get('name', player.get('username', '')),
            "user_id": current_user_id,
            "rating": current_rating,
            "rating_diff": rating_diff,
            "peak": player.get('peak_rating', 0),
            "wins": player.get('wins', 0),
            "games": player.get('games', 0),
        })

    path = os.path.join("puppeteer-leaderboard", "data", f"week{current_week}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(leaderboard_list, f, ensure_ascii=False, indent=2)
    
    print("\n=== Final leaderboard data ===")
    print(f"Saved {len(leaderboard_list)} players to {path}")
    print("First few entries:", leaderboard_list[:3])

    # If it's Sunday, save current data as base for next week
    current_date = datetime.now()
    if current_date.weekday() == 6:  # 6 is Sunday
        next_week = current_week + 1
        next_week_path = os.path.join("puppeteer-leaderboard", "data", f"week{next_week}.json")
        
        # Prepare data for next week with user_ids and correct initial rating_diff
        next_week_data = []
        for player in current_players:
            next_week_data.append({
                "name": player.get('name', player.get('username', '')),
                "user_id": player.get('user_id'),
                "rating": player.get('rating', 0),
                "rating_diff": 0,  # Initialize with 0 for next week
                "peak": player.get('peak_rating', 0),
                "wins": player.get('wins', 0),
                "games": player.get('games', 0),
            })
        
        with open(next_week_path, "w", encoding="utf-8") as f:
            json.dump(next_week_data, f, ensure_ascii=False, indent=2)
        print(f"Saved current data as week{next_week}.json for next week's comparison")


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
                
                # If previous data doesn't have user_ids, update it with current API data
                if previous_data and not any('user_id' in player for player in previous_data):
                    print("Updating previous week's data with user IDs from API")
                    updated_previous_data = []
                    for prev_player in previous_data:
                        # Try to find matching player in current API data
                        matching_player = next(
                            (p for p in current_data.get('players', []) 
                             if p.get('name', p.get('username', '')).lower() == prev_player.get('name', '').lower()),
                            None
                        )
                        if matching_player:
                            prev_player['user_id'] = matching_player.get('user_id')
                        updated_previous_data.append(prev_player)
                    
                    # Save updated previous data
                    with open(prev_path, "w", encoding="utf-8") as f:
                        json.dump(updated_previous_data, f, ensure_ascii=False, indent=2)
                    previous_data = updated_previous_data

        # Write current data to JSON
        write_leaderboard_json(current_data, previous_data, current_week)

        # Run Puppeteer script with current week number
        render_path = os.path.join("puppeteer-leaderboard", "src", "render.js")
        env = os.environ.copy()
        env["CURRENT_WEEK"] = str(current_week)
        subprocess.run(["node", render_path], check=True, env=env)

        # Send PNG
        img_path = os.path.join("puppeteer-leaderboard", "output", "leaderboard.png")
        if not os.path.exists(img_path):
            await ctx.send("Could not find the generated image.")
            return

        file = discord.File(img_path, filename="leaderboard.png")
        await ctx.send("Here is the updated leaderboard:", file=file)

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
