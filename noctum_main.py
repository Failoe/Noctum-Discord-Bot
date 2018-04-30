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
import traceback

__version__ = 0.3
os.system("title " + "Noctum Bot v{}".format(__version__))
logging.basicConfig(level=logging.ERROR)
description = "Noctum bot for OP Ark's Discord"

config = configparser.ConfigParser()
config.read('noctum.config')


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

cogs_dir = "cogs"

# Here we load our extensions(cogs) that are located in the cogs directory. Any file in here attempts to load.
if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in os.listdir(cogs_dir) if os.path.isfile(os.path.join(cogs_dir, f))]:
        try:
            client.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()


@client.event
async def on_ready():
    print(f'Logged in as: {client.user.name}. ID: {client.user.id}\nVersion: {discord.__version__}')
    print('------')

    # This code updates the CTA header to show the player counts
    await client.wait_until_ready()
    await asyncio.sleep(3)

    # This updates the Conquer the Ark channel with the currently online players
    # Change this to the follow background process style
    # https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py
    while not client.is_closed:
        channel = client.get_channel('391298871768121344')
        try:
            steamresult = steamplayers("objectivelyperfect.com", 27015)
            steamresult = "v{1} | {0}".format(steamresult[1], steamresult[2])
        except:
            steamresult = "I can't find the server. ¯\_(ツ)_/¯"
        await client.edit_channel(channel, topic=steamresult)


@client.event
async def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0.mention} to {1}!'
    await server.send(fmt.format(member, "OP"))


@client.command(pass_context=True, hidden=True)
async def run_sql(ctx, arg1, *arg2):
    """Runs arbitrary sql"""
    if ctx.guild.owner == ctx.author:
        if arg1 == "pgsql":
            pass
        elif arg1 == "sqlite":
            conn = sqlite3.connect(config['sqlite']['path'])
            cur = conn.cursor()
            cur.execute(" ".join(arg2))
            conn.commit()
            cur.close()
            conn.close()


while True:
    try:
        client.run(config['auth']['discord_token'])
    except ConnectionResetError as e:
        print(e)