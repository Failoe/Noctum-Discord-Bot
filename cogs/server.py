from discord.ext import commands
import datetime

class ServerCog:
	def __init__(self, bot):
		self.bot = bot


	@commands.command(name='servertime')
	async def servertime(self, ctx):
	    """Show the current time on the server"""
	    await ctx.send("It is " + datetime.datetime.now().strftime("%I:%M %p PST") + ".")


def setup(bot):
	bot.add_cog(ServerCog(bot))
