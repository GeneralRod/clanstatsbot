import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"{member.mention} has been kicked. Reason: {reason if reason else 'No reason provided'}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick {member.mention}: {str(e)}")

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"{member.mention} has been banned. Reason: {reason if reason else 'No reason provided'}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban {member.mention}: {str(e)}")

    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
        try:
            timeout_until = discord.utils.utcnow() + timedelta(seconds=duration)
            await member.timeout(timeout_until, reason=reason)
            await interaction.response.send_message(f"{member.mention} has been timed out for {duration} seconds. Reason: {reason if reason else 'No reason provided'}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout {member.mention}: {str(e)}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
