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
import sqlite3
from tabulate import tabulate
import operator

__version__ = 0.3
os.system("title " + "Noctum Bot v{}".format(__version__))
logging.basicConfig(level=logging.ERROR)
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


def armory_guild_update(context):
    page = requests.get('http://armory.twinstar.cz/guild-info.xml?r=Kronos+III&gn=Objectively+Perfect')
    soup = BeautifulSoup(page.content, "html5lib")

    characters = soup.find_all('character')
    character_list = [character['name'].lower() for character in characters]
    conn = sqlite3.connect(config['sqlite']['path'])
    cur = conn.cursor()

    db_char_list = [x[0] for x in cur.execute("SELECT name FROM wow_char_info;").fetchall()]

    for char in db_char_list:
        if char not in character_list:
            print("Deleting {} from database because they are no longer in the guild.".format(char))
            cur.execute("DELETE FROM wow_char_info WHERE name=?", (char,))
            cur.execute("DELETE FROM wow_chars WHERE char_name=?", (char,))
            conn.commit()
    for character in character_list:
        char_info = armory_char_query(character)
        cur.execute("""
                    INSERT OR REPLACE INTO wow_char_info (name, level, race, class, lastmodified, prof1, prof1_level, prof2, prof2_level)
                    VALUES ('{0}', {level}, '{race}', '{class}', '{lastmodified}', '{profession1[0]}', {profession1[1]}, '{profession2[0]}', '{profession2[1]}');
                    """.format(character, **char_info)
                    )
        conn.commit()
    cur.close()
    conn.close()


def armory_char_query(charname):

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
    char_dict['profession1'] = (professions[0]['key'], professions[0]['value'])
    char_dict['profession2'] = (professions[1]['key'], professions[1]['value'])

    return char_dict

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
    # Sets the Noctum's status to playing the following game
    # game = discord.Game(name='with data')
    # await client.change_presence(status=discord.Status.online, game=game)

    # This code updates the CTA header to show the player counts
    await client.wait_until_ready()
    await asyncio.sleep(3)

    # This updates the Conquer the Ark channel with the currently online players
    while not client.is_closed:
        channel = client.get_channel('391298871768121344')
        try:
            steamresult = steamplayers("objectivelyperfect.com", 27015)
            steamresult = "v{1} | {0}".format(steamresult[1], steamresult[2])
        except:
            steamresult = "I can't find the server. ¯\_(ツ)_/¯"
        await client.edit_channel(channel, topic=steamresult)


@client.event
async def on_message(message):
    print(datetime.datetime.now().time(), message.channel,
          message.author.name, "|", message.content)
    if message.author.id != 260964776945909760:  # Excludes Noctum's own messages
        if message.content.startswith('Noctum help') or message.content == ("help"):
            await message.channel.send("Hah, no.")

        if 'thunderfury' in message.content.lower():
            await message.channel.send("Did someone say [Thunderfury, Blessed Blade of the Windseeker]?")

    await client.process_commands(message)


@client.event
async def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0.mention} to {1}!'
    await server.send(fmt.format(member, "OP Ark"))


@client.command(pass_context=True)
async def run_sql(ctx, arg1, *arg2):
    if ctx.message.author.id == 119717143670423554:
        if arg1 == "pgsql":
            pass
        elif arg1 == "sqlite":
            conn = sqlite3.connect(config['sqlite']['path'])
            cur = conn.cursor()
            cur.execute(" ".join(arg2))
            conn.commit()
            cur.close()
            conn.close()


@client.command(pass_context=True)
async def query(member, message):
    dino_list = [x['name'] for x in json.loads(open('../omni2/creatures/classes.json').readline())]

    # This if statement can be removed. ;D
    if member.message.content[7:].lower() == 'failoe':
        await member.message.channel.send('HE IS EVERYWHERE! FLEE FOR YOUR LIVES!')
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
        await member.message.channel.send("```\n{}\n{}```".format(fuzzy_dino, '\n'.join(output_list)))
    else:
        await member.message.channel.send("No results.")


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
    await member.message.channel.send('```\n' + output + '```') 


@client.command(pass_context=True)
async def wow(ctx, func, char_name='', _class='', *race):
    """ Updates WoW Classic Discord Profiles
    !wow add Name
    !wow remove Name
    !wow roster (To see a list of players)
    """
    classes = ['warrior', 'rogue', 'paladin', 'mage', 'priest', 'hunter', 'druid', 'warlock']
    races = ['human', 'dwarf', 'gnome', 'night elf']

    race = " ".join(race).lower()

    if func == 'add':
        if not char_name.isalpha():
            await ctx.message.channel.send('Invalid character name. Format `!wow add Name Class Race`')
            return
        # if _class.lower() not in classes:
        #     await ctx.message.channel.send('Invalid class. Format `!wow add Name Class Race`')
        #     return
        # if race not in races:
        #     await ctx.message.channel.send('Invalid race. Format `!wow add Name Class Race`')
        #     return

        conn = sqlite3.connect(config['sqlite']['path'])
        cur = conn.cursor()
        cur.execute("""
                    INSERT OR REPLACE INTO wow_chars (discord_id, char_name)
                    VALUES ({}, '{}');
                    """.format(ctx.message.author.id, char_name.lower())
                    )
        conn.commit()
        cur.close()
        conn.close()

        await ctx.message.channel.send('Added {} to database.'.format(char_name.title()))

    elif func == 'remove':
        if not char_name.isalpha():
            await ctx.message.channel.send('Invalid character name. Format: `!wow remove Name`')
            return
        char_name = char_name.lower()

        conn = sqlite3.connect(config['sqlite']['path'])
        cur = conn.cursor()
        owner_id = cur.execute("SELECT discord_id FROM wow_chars WHERE char_name = '{}';".format(char_name)).fetchone()
        if owner_id is not None:
            owner_id = owner_id[0]
            print(owner_id)
            if owner_id == ctx.message.author.id:
                cur.execute("DELETE FROM wow_chars WHERE char_name = '{}' and discord_id = {};".format(char_name, ctx.message.author.id))
                conn.commit()
                await ctx.message.channel.send('Deleted {}.'.format(char_name.title()))    
        else:
            await ctx.message.channel.send('You can\'t remove other people\'s characters.')
        conn.close()

    elif func == 'roster':
        roster_message = await ctx.message.channel.send('Updating database...')
        try:
            armory_guild_update(ctx)
        except Exception as e:
            await ctx.message.channel.send('Something broke while updating the database.\n```{}```'.format(e))

        conn = sqlite3.connect(config['sqlite']['path'])
        cur = conn.cursor()
        cur.execute("SELECT discord_id, name, class, wow_char_info.level FROM wow_char_info LEFT JOIN wow_chars ON name=char_name;")
        rows = cur.fetchall()
        rows = [list(row) for row in rows]
        for row in rows:
            if row[0]:
                row[0] = client.get_user(row[0]).display_name

        rows.sort(key = operator.itemgetter(3), reverse=True)
        rows.sort(key = operator.itemgetter(2))

        output = tabulate(rows, headers=['Discord ID', 'Name', 'Class', 'Lvl'])
        conn.close()
        await roster_message.edit(content='```{}```'.format(output).title())

    elif func == 'fullroster':
        conn = sqlite3.connect(config['sqlite']['path'])
        cur = conn.cursor()
        cur.execute("SELECT discord_id, name, class, wow_char_info.race, wow_char_info.level FROM wow_chars LEFT JOIN wow_char_info ON char_name=name;")
        rows = cur.fetchall()
        rows = [list(row) for row in rows]
        for row in rows:
            row[0] = client.get_user(row[0]).display_name

        rows.sort(key = operator.itemgetter(3), reverse=True)
        rows.sort(key = operator.itemgetter(2))

        output = tabulate(rows, headers=['User', 'Name', 'Class', 'Race', 'Lvl'])
        conn.close()
        await ctx.message.channel.send('```{}```'.format(output).title())

    elif func == 'update':
        try:
            armory_guild_update(ctx)
            await ctx.message.channel.send('Guild database updated.')
        except Exception as e:
            await ctx.message.channel.send('Something broke.\n```{}```'.format(e))

    elif func == 'professions' or func == 'profs':
        conn = sqlite3.connect(config['sqlite']['path'])
        cur = conn.cursor()
        cur.execute("""
                SELECT discord_id, name, prof1, prof1_level FROM wow_char_info LEFT JOIN wow_chars ON char_name=name
                UNION ALL
                SELECT discord_id, name, prof2, prof2_level FROM wow_char_info LEFT JOIN wow_chars ON char_name=name;"""
                )
        rows = cur.fetchall()
        conn.close()

        rows = [list(row) for row in rows]

        rows.sort(key = operator.itemgetter(3), reverse=True)
        rows.sort(key = operator.itemgetter(2))

        header = ""
        row_output = []
        for row in rows:
            if row[0]:
                row[0] = client.get_user(row[0]).display_name

            if row[2] != header:
                header = row[2]
                row_output.append([])
                row_output.append([header.upper()])

            row[1] = row[1].title() #Makes the player name titlecase
            row.pop(2) #This removes the name of the profession
            row.pop(0) #This removes the Discord Username
            row_output.append(row)
        output = tabulate(row_output)
        await ctx.message.channel.send('```{}```'.format(output))

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
        await member.message.channel.send("Added alert for level {}+ {}".format(dino_level, fuzzy_dino))
    except ValueError:
        await member.message.channel.send("You did something wrong.")


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

        await member.message.channel.send("Deleted alert for {}".format(fuzzy_dino))
    except ValueError:
        await member.message.channel.send("You did something wrong.")


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
    await member.message.channel.send("\n".join(message_list))


@client.command(pass_context=True)
async def lastupdate(member):
    conn = pgsql_connect(config)
    cur = conn.cursor()
    cur.execute('SELECT datestamp FROM players LIMIT 1')
    await member.message.channel.send("Last database update: {}".format(cur.fetchall()[0][0]))
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
        await ctx.message.channel.send(steamresult[0])

while True:
    try:
        client.run(config['auth']['discord_token'])
    except ConnectionResetError as e:
        print(e)