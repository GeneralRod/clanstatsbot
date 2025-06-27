from discord.ext import commands

class Reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if 'nigga' in message.content.lower():
            await message.channel.send("🐒")

        if 'nigger' in message.content.lower():
            await message.channel.send("🐒")

        if 'jane' in message.content.lower():
            await message.channel.send("https://only-fans.uk/JaneLeak")


async def setup(bot):
    await bot.add_cog(Reactions(bot))
