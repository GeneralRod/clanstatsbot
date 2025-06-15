import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import utcnow
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.describe(target_user="The user you want to timeout", duration="Duration of timeout", reason="Reason for timeout")
    @app_commands.choices(duration=[
        app_commands.Choice(name="5 seconds", value=5),
        app_commands.Choice(name="1 minute", value=60),
        app_commands.Choice(name="5 minutes", value=300),
        app_commands.Choice(name="10 minutes", value=600),
        app_commands.Choice(name="1 hour", value=3600),
        app_commands.Choice(name="1 day", value=86400),
        app_commands.Choice(name="7 days", value=604800),
        app_commands.Choice(name="28 days (max)", value=2419200),
    ])
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, target_user: discord.Member, duration: app_commands.Choice[int], reason: str = "No reason provided"):
        duration_value = duration.value

        if duration_value < 5 or duration_value > 2419200:
            await interaction.response.send_message("Timeout duration must be between 5 seconds and 28 days.", ephemeral=True)
            return

        if target_user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot timeout this user because they have the same or higher role than you.", ephemeral=True)
            return

        if target_user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot timeout this user because they have the same or higher role than me.", ephemeral=True)
            return

        timeout_until = utcnow() + datetime.timedelta(seconds=duration_value)
        try:
            await target_user.timeout(timeout_until, reason=reason)
            await interaction.response.send_message(f"{target_user.mention} has been timed out for {duration_value} seconds.\nReason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout user: {e}", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(target_user="The user you want to kick", reason="Reason for kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, target_user: discord.Member, reason: str = "No reason provided"):
        if target_user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot kick this user because they have the same or higher role than you.", ephemeral=True)
            return

        if target_user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot kick this user because they have the same or higher role than me.", ephemeral=True)
            return

        try:
            await target_user.kick(reason=reason)
            await interaction.response.send_message(f"{target_user.mention} has been kicked.\nReason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick user: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(target_user="The user you want to ban", reason="Reason for ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, target_user: discord.Member, reason: str = "No reason provided"):
        if target_user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot ban this user because they have the same or higher role than you.", ephemeral=True)
            return

        if target_user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot ban this user because they have the same or higher role than me.", ephemeral=True)
            return

        try:
            await target_user.ban(reason=reason)
            await interaction.response.send_message(f"{target_user.mention} has been banned.\nReason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban user: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
