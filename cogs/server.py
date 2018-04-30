from discord.ext import commands
import datetime

class ServerCog:
	def __init__(self, bot):
		self.bot = bot

	@commands.group(name='servertime')
	async def servertime(self, ctx):
	    """Show the current time on the server"""
	    if ctx.invoked_subcommand is None:
		    await ctx.send("It is " + datetime.datetime.now().strftime("%I:%M %p PST") + ".")


	@commands.command()
	async def ownercheck(self, ctx):
		if ctx.guild.owner == ctx.author:
			await ctx.send("Access Granted.")
		else:
			await ctx.send("Access Denied.")

	async def on_message(self, ctx):
		print(datetime.datetime.now().time(), ctx.channel,
			  ctx.author.name, "|", ctx.content)
		if ctx.author == self.bot.user: # Excludes Noctum's own messages
			return
		if ctx.content.startswith('Noctum help') or ctx.content == ("help"):
			await ctx.channel.send("Hah, no.")

		if 'thunderfury' in ctx.content.lower():
			await ctx.channel.send("Did someone say [Thunderfury, Blessed Blade of the Windseeker]?")


def setup(bot):
	bot.add_cog(ServerCog(bot))
