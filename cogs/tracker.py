from discord.ext import commands
import datetime

class TrackerCog:
	def __init__(self, bot):
		self.bot = bot

	@commands.group()
	async def tracker(self, ctx):
	    if ctx.invoked_subcommand is None:
		    pass

	@tracker.command()
	async def info(self, ctx):
		await ctx.send("There should be something useful here.")

	async def on_ready(self, ctx):
		pass

	async def on_message(self, ctx):
		"""Record messages"""
		pass
		# author_id

		# content

		# channel

		# embeds

		# mentions

		# channel_mentions

		# message id

		# attachments

		# reactions

		# guild id

		# creation time

	async def on_message_delete(self, ctx):
		pass

	async def on_message_edit(self, before, after):
		pass

	async def on_reaction_add(self, ctx):
		pass

	async def on_reaction_remove(self, ctx):
		pass

	async def on_reaction_clear(self, ctx):
		pass

	async def on_member_update(self, before, after):
		pass

	async def on_guild_join(self, ctx):
		pass

	async def on_guild_remove(self, ctx):
		pass

	async def on_guild_update(self, ctx):
		pass

	async def on_member_join(self, ctx):
		pass

	async def on_member_remove(self, ctx):
		pass

	async def on_guild_role_create(self, ctx):
		pass

	async def on_guild_role_delete(self, ctx):
		pass

	async def on_guild_role_update(self, ctx):
		pass

	async def on_guild_emojis_update(self, ctx):
		pass

	async def on_member_ban(self, ctx):
		pass

	async def on_member_unban(self, ctx):
		pass

	async def on_guild_channel_create(self, ctx):
		pass

	async def on_guild_channel_delete(self, ctx):
		pass



def setup(bot):
	bot.add_cog(TrackerCog(bot))
