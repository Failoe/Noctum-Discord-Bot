import discord
from discord.ext import commands
import os

class OwnerCog:

    def __init__(self, bot):
        self.bot = bot
    
    # Hidden means it won't show up on the default help.
    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def cog_load(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def cog_unload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def cog_reload(self, ctx, *, cog=''):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        if not cog:
            cogs = [f.replace('.py', '') for f in os.listdir('cogs') if os.path.isfile(os.path.join('cogs', f))]
            succesful_cogs = []
            for cog_ in cogs:
                try:
                    self.bot.unload_extension("cogs." + cog_)
                    self.bot.load_extension("cogs." + cog_)
                    succesful_cogs.append(cog_)
                except Exception as e:
                    await ctx.send(f'**`ERROR: Cog: {cog_}`** {type(e).__name__} - {e}')
            await ctx.send(f'**`{"SUCCESS" if succesful_cogs else "FAILED"}:`** {", ".join(succesful_cogs)}')
            return

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')


    @commands.command(name='change_activity', hidden=True, aliases=['ca'])
    @commands.is_owner()
    async def change_activity(self, ctx, *, activity: str):
        """Changes the bot's current activity"""
        try:
            game = discord.Game(activity)
            await ctx.bot.change_presence(status=discord.Status.idle, activity=game)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'**`SUCCESS`**: Changed activity to `{activity}`')


    async def on_message(self, ctx):
        if ctx.author == self.bot.user: # Excludes Noctum's own messages
            return
        if ctx.content.lower().startswith('reee'):
            await ctx.channel.send("REEEEEEEEE!!!!!")


def setup(bot):
    bot.add_cog(OwnerCog(bot))
