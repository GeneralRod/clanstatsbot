from discord.ext import commands

class Reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if 'nigger' in message.content.lower():
            await message.channel.send("🐒")

        if 'nigga' in message.content.lower():
            await message.channel.send("🐒")

        if 'niggers' in message.content.lower():
            await message.channel.send("🐒")

        if 'niggas' in message.content.lower():
            await message.channel.send("🐒")

        if 'niggr' in message.content.lower():
            await message.channel.send("🐒")

        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(Reactions(bot))
