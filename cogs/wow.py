from discord.ext import commands
import sqlite3
import configparser
from tabulate import tabulate
import operator
from bs4 import BeautifulSoup
import requests


class WoWCog:
	config = configparser.ConfigParser()
	config.read('noctum.config')

	def __init__(self, bot):
		self.bot = bot

	def armory_guild_update(self, context):
		try:
			page = requests.get('http://armory.twinstar.cz/guild-info.xml?r=Kronos+III&gn=Objectively+Perfect', timeout=5)
		except:
			context.send("Unable to query Kronos Database.")
			return
		soup = BeautifulSoup(page.content, "html5lib")

		characters = soup.find_all('character')
		character_list = [character['name'].lower() for character in characters]
		conn = sqlite3.connect(self.config['sqlite']['path'])
		cur = conn.cursor()

		db_char_list = [x[0] for x in cur.execute("SELECT name FROM wow_char_info;").fetchall()]

		for char in db_char_list:
			if char not in character_list:
				print("Deleting {} from database because they are no longer in the guild.".format(char))
				cur.execute("DELETE FROM wow_char_info WHERE name=?", (char,))
				cur.execute("DELETE FROM wow_chars WHERE char_name=?", (char,))
				conn.commit()

		for character in character_list:
			char_info = self.armory_char_query(character)
			cur.execute("""
						INSERT OR REPLACE INTO wow_char_info (name, level, race, class, lastmodified, prof1, prof1_level, prof2, prof2_level)
						VALUES ('{0}', {level}, '{race}', '{class}', '{lastmodified}', '{profession1[0]}', {profession1[1]}, '{profession2[0]}', '{profession2[1]}');
						""".format(character, **char_info)
						)
			conn.commit()
		cur.close()
		conn.close()


	def armory_char_query(self, charname):

		# reason 2 = doesn't exist
		# reason 6 = too low level

		page = requests.get('http://armory.twinstar.cz/character-sheet.xml?r=Kronos+III&cn={}&gn=Objectively+Perfect'.format(charname))
		soup = BeautifulSoup(page.content, "html5lib")

		char_dict = {}

		char_dict['level'] = soup.find("character")['level']
		char_dict['race'] = soup.find("character")['race']
		char_dict['class'] = soup.find("character")['class'][0]
		char_dict['lastmodified'] = soup.find("character")['lastmodified']
		professions = soup.professions.find_all('skill')

		try:
			char_dict['profession1'] = (professions[0].get('key'), professions[0].get('value'))
		except:
			char_dict['profession1'] = (None, None)

		try:
			char_dict['profession2'] = (professions[1].get('key'), professions[1].get('value'))
		except:
			char_dict['profession2'] = (None, None)

		return char_dict


	@commands.group(name='wow', pass_context=True)
	async def wow(self, ctx):
		""" Updates WoW Kronos Profiles"""
		classes = ['warrior', 'rogue', 'paladin', 'mage', 'priest', 'hunter', 'druid', 'warlock']
		races = ['human', 'dwarf', 'gnome', 'night elf']


	@wow.command()
	async def add(self, ctx, *, char_name):
		if not char_name.isalpha():
			await ctx.send(f'Invalid character name `{char_name}`. Format `!wow add Name`')
			return

		conn = sqlite3.connect(self.config['sqlite']['path'])
		cur = conn.cursor()
		cur.execute("""
					INSERT OR REPLACE INTO wow_chars (discord_id, char_name)
					VALUES ({}, '{}');
					""".format(ctx.message.author.id, char_name.lower())
					)
		conn.commit()
		cur.close()
		conn.close()
		await ctx.send(f"Added {char_name} to the roster.")


	@wow.command()
	async def remove(self, ctx, *, char_name):
		if not char_name.isalpha():
			await ctx.message.channel.send('Invalid character name. Format: `!wow remove Name`')
			return
		char_name = char_name.lower()

		conn = sqlite3.connect(self.config['sqlite']['path'])
		cur = conn.cursor()
		owner_id = cur.execute("SELECT discord_id FROM wow_chars WHERE char_name = '{}';".format(char_name)).fetchone()
		if owner_id is not None:
			owner_id = owner_id[0]
			if owner_id == ctx.message.author.id:
				cur.execute("DELETE FROM wow_chars WHERE char_name = '{}' and discord_id = {};".format(char_name, ctx.message.author.id))
				conn.commit()
				await ctx.message.channel.send('Deleted {}.'.format(char_name.title()))    
		else:
			await ctx.message.channel.send('You can\'t remove other people\'s characters.')
		conn.close()

	@wow.command()
	async def fullroster(self, ctx):
		conn = sqlite3.connect(self.config['sqlite']['path'])
		cur = conn.cursor()
		cur.execute("SELECT discord_id, name, class, wow_char_info.race, wow_char_info.level FROM wow_chars LEFT JOIN wow_char_info ON char_name=name;")
		rows = cur.fetchall()
		rows = [list(row) for row in rows]
		for row in rows:
			row[0] = ctx.guild.get_member(row[0]).display_name if row[0] else ''

		output = tabulate(rows, headers=['User', 'Name', 'Class', 'Race', 'Lvl'])
		conn.close()
		await ctx.send('```{}```'.format(output).title())


	@wow.command()
	async def roster(self, ctx):
		roster_message = await ctx.message.channel.send('Updating database...')
		try:
			self.armory_guild_update(ctx)
		except Exception as e:
			await ctx.message.channel.send('Something broke while updating the database.\n```{}```'.format(e))

		conn = sqlite3.connect(self.config['sqlite']['path'])
		cur = conn.cursor()
		cur.execute("SELECT name, class, wow_char_info.level FROM wow_char_info LEFT JOIN wow_chars ON name=char_name;")
		rows = cur.fetchall()
		rows = [list(row) for row in rows]

		rows.sort(key = operator.itemgetter(2), reverse=True)
		rows.sort(key = operator.itemgetter(1))

		output = tabulate(rows, headers=['Name', 'Class', 'Lvl'])
		conn.close()
		await roster_message.edit(content='```{}```'.format(output).title())

	@wow.command()
	async def update(self, ctx):
		try:
			self.armory_guild_update(ctx)
			await ctx.send('Guild database updated.')
		except Exception as e:
			await ctx.send('Something broke.\n```{}```'.format(e))

	@wow.command(aliases=['professions'])
	async def profs(self, ctx):
		conn = sqlite3.connect(self.config['sqlite']['path'])
		cur = conn.cursor()
		cur.execute("""
				SELECT name, prof1, prof1_level FROM wow_char_info LEFT JOIN wow_chars ON char_name=name
				UNION ALL
				SELECT name, prof2, prof2_level FROM wow_char_info LEFT JOIN wow_chars ON char_name=name;"""
				)
		rows = cur.fetchall()
		conn.close()

		rows = [list(row) for row in rows if row[1] != 'None']

		rows.sort(key = operator.itemgetter(2), reverse=True)
		rows.sort(key = operator.itemgetter(1))

		header = ""
		row_output = []
		for row in rows:
			if row[1] != header:
				header = row[1]
				row_output.append([])
				row_output.append([header.upper()])

			row[0] = row[0].title() #Makes the player name titlecase
			row.pop(1) #This removes the name of the profession
			row_output.append(row)
		output = tabulate(row_output)
		await ctx.message.channel.send('```{}```'.format(output))


	@wow.command(name='search')
	async def search():
		pass

def setup(bot):
	bot.add_cog(WoWCog(bot))
