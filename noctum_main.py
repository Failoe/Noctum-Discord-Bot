#!python3

import valve.source.a2s
import os
import random
import discord
import asyncio
from discord.ext import commands
import re
import datetime
from time import sleep

from mcstatus import MinecraftServer
from bs4 import BeautifulSoup
import requests
import psycopg2
from fuzzywuzzy import process
import json
import logging
import configparser
from noctum_utils.db_utils import pgsql_connect

__version__ = 0.3
os.system("title " + "Noctum Bot v{}".format(__version__))
logging.basicConfig(level=logging.INFO)
description = "Noctum bot for OP Ark's Discord"

config = configparser.ConfigParser()
config.read('noctum.config')


announced_dinos = []


def item_audit(conn, item):
    cur = conn.cursor()
    cur.execute(cur.mogrify("SELECT SUM(quantity) FROM items WHERE item_name = '%s' and TribeID = '1250143954'" % item.title()))
    return cur.fetchone()[0]


def dino_alert(creature, level):
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


def ark_add_alert(user, dino, level):
    conn = pgsql_connect(config)
    cur = conn.cursor()
    cur.execute(cur.mogrify(""" INSERT INTO ark_alerts (user_id, dino, level)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (dino) DO UPDATE 
                    SET level = %s, user_id = %s""",
                    (user, dino, level, level, user)))
    conn.commit()
    cur.close()
    conn.close()


def ark_alert_query(channel, client):
    output = []
    conn = pgsql_connect(config)
    cur = conn.cursor()
    cur.execute("SELECT dino, level FROM ark_alerts")
    alerts = cur.fetchall()
    # print(alerts)
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


def steamplayers(address="objectivelyperfect.com", port=27015):
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


def rolecheck(member):
    """Returns whether or not a user has the Ark Admin role."""
    rolelist = []
    for role in member.roles:
        rolelist.append(role.name)
    if 'Admin' in rolelist or 'Mod' in rolelist:
        return True
    else:
        return False


client = commands.Bot(command_prefix=['!'], description=description)


@client.event
async def on_ready():
    print('Logged in as: {}. ID: {}'.format(client.user.name, client.user.id))
    print('------')
    await client.change_presence(game=discord.Game(name='with things she can\'t control'))

    # This code updates the CTA header to show the player counts
    await client.wait_until_ready()
    await asyncio.sleep(3)
    while not client.is_closed:
        channel = client.get_channel('391298871768121344')
        try:
            steamresult = steamplayers("objectivelyperfect.com", 27015)
            steamresult = "v{1} | {0}".format(steamresult[1], steamresult[2])
        except:
            steamresult = "I can't find the server. ¯\_(ツ)_/¯"
        await client.edit_channel(channel, topic=steamresult)

        # for dino_alert in ark_alert_query(channel, client):
        #     await client.send_message(channel, dino_alert)
        # await asyncio.sleep(300)


@client.event
async def on_message(message):
    print(datetime.datetime.now().time(), message.channel,
          message.author.name, "|", message.content)
    if message.author.id != "260964776945909760":  # Excludes Noctum's own messages
        if message.content.startswith('Noctum help') or message.content == ("help"):
            await client.send_message(message.channel, "Hah, no.")
        # elif message.content.startswith('#') and message.author.id == "119717143670423554":
        #     await client.delete_message(message)
        #     await client.send_message(message.channel, message.content[1:])
        elif message.content.startswith('$$') and message.author.id == "119717143670423554":
            output_channel = "bot"
            regex = re.compile(r"\$(.+?) (.*)")
            output_channel = regex.match(message.content).group(1)
            print(output_channel)
            output_text = regex.match(message.content).group(2)
            try:
                for server in client.servers:
                    for channel in server.channels:
                        if channel.name == output_channel:
                            output_channel = channel
                await client.send_message(client.get_channel(output_channel[2:-1]), output_text)
            except:
                await client.send_message(message.channel, "Not a real channel nerd.")
        elif message.content.lower().startswith('noctum') and "promise to be good" in message.content:
            await client.send_message(message.channel, "You may enter.")
            await client.send_message(message.author, "The password is `conquer`.")
    await client.process_commands(message)


@client.event
async def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0.mention} to {1}!'
    await client.send_message(server, fmt.format(member, "OP Ark"))

@client.command(pass_context=True)
async def query(member, message):
    dino_list = [x['name'] for x in json.loads(open('../omni2/creatures/classes.json').readline())]

    # This if statement can be removed. ;D
    if member.message.content[7:].lower() == 'failoe':
        await client.send_message(member.message.channel, 'HE IS EVERYWHERE! FLEE FOR YOUR LIVES!')
        return

    if member.message.content[7:] in dino_list:
        fuzzy_dino = member.message.content[7:]
    else:
        fuzzy_dino = process.extractOne(member.message.content[7:], dino_list)[0]

    conn = pgsql_connect(config)
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
        await client.send_message(member.message.channel, "```\n{}\n{}```".format(fuzzy_dino, '\n'.join(output_list)))
    else:
        await client.send_message(member.message.channel, "No results.")


@client.command(pass_context=True)
async def list_alerts(member):
    """ Lists the currently active Ark dino alerts """
    conn = pgsql_connect(config)
    cur = conn.cursor()
    cur.execute("""SELECT dino, level FROM ark_alerts""")
    alerts = cur.fetchall()
    cur.close()
    conn.close()
    print(alerts)
    output = '\n'.join(['{} {}'.format(' '*(3-len(str(level)))+str(level), dino) for dino, level in alerts])
    await client.send_message(member.message.channel, '```\n' + output + '```') 


@client.command(pass_context=True)
async def add_alert(member, message):
    """ Adds a alert for a dinos that spawn above a given level.  Format is: !add_alert Rex 100 """
    dino_list = [x['name'] for x in json.loads(open('../omni2/creatures/classes.json').readline())]
    command_text = member.message.content[11:]
    try:
        dino_name, dino_level = command_text.split(' ')
        if dino_name in dino_list:
            fuzzy_dino = dino_name
        else:
            fuzzy_dino = process.extractOne(dino_name, dino_list)[0]
        ark_add_alert(member.message.author.id, fuzzy_dino, int(dino_level))
        await client.send_message(member.message.channel, "Added alert for level {}+ {}".format(dino_level, fuzzy_dino))
    except ValueError:
        await client.send_message(member.message.channel, "You did something wrong.")


@client.command(pass_context=True)
async def remove_alert(member, message):
    """ Removes alerts for a dino type.  Format is: !remove_alert Rex """
    dino_list = [x['name'] for x in json.loads(open('../omni2/creatures/classes.json').readline())]
    dino_name = member.message.content[14:]
    try:
        if dino_name in dino_list:
            fuzzy_dino = dino_name
        else:
            fuzzy_dino = process.extractOne(dino_name, dino_list)[0]

        conn = pgsql_connect(config)
        cur = conn.cursor()
        cur.execute(cur.mogrify("""DELETE FROM ark_alerts
                                    WHERE dino = '%s';""" % fuzzy_dino))
        conn.commit()
        cur.close()
        conn.close()

        await client.send_message(member.message.channel, "Deleted alert for {}".format(fuzzy_dino))
    except ValueError:
        await client.send_message(member.message.channel, "You did something wrong.")


@client.command(pass_context=True)
async def item(member):
    conn = pgsql_connect(config)
    items = member.message.content[6:].split(',')
    message_list = []
    for item_name in items:
        item_name = item_name.strip()
        sql_results = item_audit(conn, item_name)
        if sql_results:
            message_list.append("{}: {}".format(item_name.title(), sql_results))
        else:
            message_list.append("Ain't got no {}.".format(item_name))
    await client.send_message(member.message.channel, "\n".join(message_list))


@client.command(pass_context=True)
async def lastupdate(member):
    conn = pgsql_connect(config)
    cur = conn.cursor()
    cur.execute('SELECT datestamp FROM players LIMIT 1')
    await client.send_message(member.message.channel, "Last database update: {}".format(cur.fetchall()[0][0]))
    conn.close()


@client.command()
async def joined(member: discord.Member):
    """Says when a member joined."""
    await client.say('{0.name} joined on {0.joined_at}'.format(member))


@client.command()
async def servertime():
    """Show the current time on the server"""
    await client.say("It is " + datetime.datetime.now().strftime("%I:%M %p PST") + ".")


@client.command()
async def join():
    """Provides server connection links"""
    await client.say("<:rex:274395290214072321> Join Conquer the Ark: steam://connect/73.118.210.163:27015/")


@client.group(pass_context=True)
async def online(ctx):
    """Shows online players. Usage: !online island|scorched"""
    if ctx.invoked_subcommand is None:
        steamresult = steamplayers("objectivelyperfect.com", 27015)
        await client.send_message(ctx.message.channel, steamresult[0])


client.run(config['auth']['discord_token'])
