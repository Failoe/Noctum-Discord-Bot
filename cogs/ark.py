from discord.ext import commands
import json
from fuzzywuzzy import process
from noctum_utils.db_utils import pgsql_connect
import configparser
import valve.source.a2s
import re


class ArkCog:
	config = configparser.ConfigParser()
	config.read('noctum.config')


	def __init__(self, bot):
		self.bot = bot


	def item_audit(self, conn, item):
		cur = conn.cursor()
		cur.execute(cur.mogrify("SELECT SUM(quantity) FROM items WHERE item_name = '%s' and TribeID = '1250143954'" % item.title()))
		return cur.fetchone()[0]


	def dino_alert(self, creature, level):
		conn = pgsql_connect(config)
		cur = conn.cursor()

		cur.execute(""" SELECT baselevel, lat, lon, gender, wild_health, wild_stamina, wild_melee, id
						FROM creatures
						WHERE type='{0}'
						AND tamed IS NULL
						AND baselevel >= {1}""".format(creature, level))

		rows = cur.fetchall()
		conn.close()
		return rows


	def ark_add_alert(self, user, dino, level):
		"""Adds an alert for dinos over the provided level."""
		conn = pgsql_connect(self.config)
		cur = conn.cursor()
		cur.execute(cur.mogrify(""" INSERT INTO ark_alerts (user_id, dino, level)
						VALUES (%s, %s, %s)
						ON CONFLICT (dino) DO UPDATE 
						SET level = %s, user_id = %s""",
						(user, dino, level, level, user)))
		conn.commit()
		cur.close()
		conn.close()


	def ark_alert_query(self, channel, client):
		output = []
		conn = pgsql_connect(config)
		cur = conn.cursor()
		cur.execute("SELECT dino, level FROM ark_alerts")
		alerts = cur.fetchall()
		for alert in alerts:
			creature, level = alert
			cur = conn.cursor()

			cur.execute(""" SELECT baselevel, lat, lon, gender, wild_health, wild_stamina, wild_melee, id
							FROM creatures
							WHERE type='{0}'
							AND tamed IS NULL
							AND baselevel >= {1}""".format(creature, level))

			rows = cur.fetchall()
			if len(rows) > 0:
				for dino in rows:
					if dino[7] not in announced_dinos:
						dino_message = "Level {0} {3} {7} spotted. {1}, {2}\n{4} HP | {5} Stam | {6} Melee".format(
							dino[0], round(dino[1], 1), round(dino[2], 1), dino[3], dino[4], dino[5], dino[6], creature)
						# baselevel, lat, lon, gender, wild_health, wild_stamina, wild_melee
						# await client.send_message(channel, dino_message)
						output.append(dino_message)
						announced_dinos.append(dino[7])

		cur.close()
		conn.close()
		return output


	def steamplayers(self, address="objectivelyperfect.com", port=27015):
		"""Returns a string with the list of players for a given server."""
		SERVER_ADDRESS = (address, port)

		server = valve.source.a2s.ServerQuerier(SERVER_ADDRESS)
		info = server.info()

		players = server.players()

		header = ("{}:\n".format(info["server_name"]))
		ark_version = re.search(r"\(v(\d+\.\d+)", info["server_name"]).group(1)

		for x in players["players"]:
			if x['name'] != "":
				m, s = divmod(x['duration'], 60)
				h, m = divmod(m, 60)
				x['duration'] = "{}h".format(round(h + m/60, 1))

		topic_list = ', '.join(["{}".format(x['name'][:7]+"..." if len(x['name']) > 10 else x['name']) for x in players["players"] if x['name'] != ""])
		topic_len = len(["{} ({})".format(x['name'], x['duration']) for x in players["players"] if x['name'] != ""])
		playerlist = '\n'.join(["{} ({})".format(x['name'], x['duration']) for x in players["players"] if x['name'] != ""])

		return "```" + header + playerlist + "```", topic_list, ark_version


	@commands.command(name='addalert')
	async def add_alert(self, member):
		"""Adds an alert for a dinos. !addalert Rex 100 """
		dino_list = [x['name'] for x in json.loads(open('../omni2/creatures/classes.json').readline())]
		command_text = member.message.content[11:]
		try:
			dino_name, dino_level = command_text.split(' ')
			if dino_name in dino_list:
				fuzzy_dino = dino_name
			else:
				fuzzy_dino = process.extractOne(dino_name, dino_list)[0]
			self.ark_add_alert(member.message.author.id, fuzzy_dino, int(dino_level))
			await member.message.channel.send("Added alert for level {}+ {}".format(dino_level, fuzzy_dino))
		except ValueError:
			await member.message.channel.send("You did something wrong.")


	@commands.command(name='removealert')
	async def remove_alert(self, member, message):
		""" Removes alerts for a dino.  !removealert Rex"""
		dino_list = [x['name'] for x in json.loads(open('../omni2/creatures/classes.json').readline())]
		dino_name = member.message.content[14:]
		try:
			if dino_name in dino_list:
				fuzzy_dino = dino_name
			else:
				fuzzy_dino = process.extractOne(dino_name, dino_list)[0]

			conn = pgsql_connect(self.config)
			cur = conn.cursor()
			cur.execute(cur.mogrify("""DELETE FROM ark_alerts
										WHERE dino = '%s';""" % fuzzy_dino))
			conn.commit()
			cur.close()
			conn.close()

			await member.message.channel.send("Deleted alert for {}".format(fuzzy_dino))
		except ValueError:
			await member.message.channel.send("You did something wrong.")


	@commands.command(name='listalerts')
	async def list_alerts(self, ctx):
		""" Lists the currently active dino alerts """
		conn = pgsql_connect(self.config)
		cur = conn.cursor()
		cur.execute("""SELECT dino, level FROM ark_alerts""")
		alerts = cur.fetchall()
		cur.close()
		conn.close()
		print(alerts)
		output = '\n'.join(['{} {}'.format(' '*(3-len(str(level)))+str(level), dino) for dino, level in alerts])
		await ctx.send('```\n' + output + '```')


	@commands.command(name='item')
	async def item(self, member):
		"""Shows item counts"""
		conn = pgsql_connect(self.config)
		items = member.message.content[6:].split(',')
		message_list = []
		for item_name in items:
			item_name = item_name.strip()
			sql_results = self.item_audit(conn, item_name)
			if sql_results:
				message_list.append("{}: {}".format(item_name.title(), sql_results))
			else:
				message_list.append("Ain't got no {}.".format(item_name))
		await member.message.channel.send("\n".join(message_list))


	@commands.command(name='lastupdate', hidden=True)
	async def lastupdate(self, ctx):
		"""Shows last database update"""
		conn = pgsql_connect(self.config)
		cur = conn.cursor()
		cur.execute('SELECT datestamp FROM players LIMIT 1')
		await ctx.send("Last database update: {}".format(cur.fetchall()[0][0]))
		conn.close()


	@commands.command(name='join')
	async def join(self, ctx):
		"""Instructions on how to join the server"""
		await ctx.send("<:rex:274395290214072321> Join Conquer the Ark: steam://connect/73.118.210.163:27015/ " \
			"If/when this fails, add 73.118.210.163:27015 to your favorite servers on the Steam client (not in Ark). " \
			"Then boot up Ark and join from your favorite servers list.  The password is `conquer`.")


	@commands.group(name='online')
	async def online(self, ctx):
		"""Shows logged in players"""
		if ctx.invoked_subcommand is None:
			steamresult = self.steamplayers("objectivelyperfect.com", 27015)
			await ctx.message.channel.send(steamresult[0])


	@commands.command(name='query')
	async def query(self, ctx):
	    """Finds wild dinos. !query Rex"""
	    dino_list = [x['name'] for x in json.loads(open('../omni2/creatures/classes.json').readline())]

	    # This if statement can be removed. ;D
	    if ctx.message.content[7:].lower() == 'failoe':
	        await ctx.message.channel.send('HE IS EVERYWHERE! FLEE FOR YOUR LIVES!')
	        return

	    if ctx.message.content[7:] in dino_list:
	        fuzzy_dino = ctx.message.content[7:]
	    else:
	        fuzzy_dino = process.extractOne(ctx.message.content[7:], dino_list)[0]

	    conn = pgsql_connect(self.config)
	    cur = conn.cursor()

	    cur.execute("""SELECT baselevel, lat, lon, gender, wild_health, wild_stamina, wild_melee, id
	            FROM creatures
	            WHERE type='{}' 
	            AND tamed IS NULL 
	            ORDER BY baselevel DESC
	            LIMIT 10""".format(fuzzy_dino))

	    rows = cur.fetchall()
	    conn.close()

	    if len(rows) > 0:
	        output_list = []
	        for dino in rows:
	            dino_message = "{0}{3}{1}, {2}[{4} HP | {5} Stam | {6} Melee]".format(
	                    str(dino[0])+" "*(4-len(str(dino[0]))),
	                    " "*(5-len(str(round(dino[1], 1))))+str(round(dino[1], 1)),
	                    str(round(dino[2], 1))+" "*(5-len(str(round(dino[2], 1)))),
	                    dino[3]+" "*(7-len(dino[3])),
	                    " "*(2-len(str(0 if dino[4] == None else dino[4])))+str(0 if dino[4] == None else dino[4]),
	                    " "*(2-len(str(0 if dino[5] == None else dino[5])))+str(0 if dino[5] == None else dino[5]),
	                    " "*(2-len(str(0 if dino[6] == None else dino[6])))+str(0 if dino[6] == None else dino[6]))
	            output_list.append(dino_message)
	        await ctx.send("```\n{}\n{}```".format(fuzzy_dino, '\n'.join(output_list)))
	    else:
	        await ctx.send("No results.")


def setup(bot):
	bot.add_cog(ArkCog(bot))
