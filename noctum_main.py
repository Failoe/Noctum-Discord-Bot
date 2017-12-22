#!python3

import valve.source.a2s
import os
import random
import discord
import asyncio
from discord.ext import commands
import re
import logging
import datetime

from mcstatus import MinecraftServer
from bs4 import BeautifulSoup
import requests

__version__ = 0.3

os.system("title " + "Noctum Bot{}".format(__version__))

# logging.basicConfig(level=logging.INFO)

description = "Noctum bot for OP Ark's Discord"


def mtg_card_link(cardname):
    page = requests.get("http://magiccards.info/query?q={}".format(cardname))
    soup = BeautifulSoup(page.content, 'html5lib')
    image_link = soup.find_all('tbody')[3].img['src']
    if "magiccards.info" not in image_link:
        return "http://magiccards.info{}".format(image_link)
    else:
        return image_link


def steamplayers(address="objectivelyperfect.com", port=27015):
    """Returns a string with the list of players for a given server."""
    SERVER_ADDRESS = (address, port)

    server = valve.source.a2s.ServerQuerier(SERVER_ADDRESS)
    info = server.info()

    players = server.players()

    header = ("{}:\n".format(info["server_name"]))

    playerlist = '\n'.join(["{} ({} minutes)".format(x['name'], int(
        x['duration'] / 60)) for x in players["players"] if x['name'] != ""])

    return "```" + header + playerlist + "```"


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
    await client.change_presence(game=discord.Game(name='god'))


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
            output_text = regex.match(message.content).group(2)
            try:
                for server in client.servers:
                    for channel in server.channels:
                        if channel.name == output_channel:
                            output_channel = channel
                await client.send_message(output_channel, output_text)
            except:
                await client.send_message(message.channel, "Not a real channel nerd.")
        elif message.content.lower().startswith('noctum') and "promise to be good" in message.content:
            await client.send_message(message.channel, "You may enter.")
            await client.send_message(message.author, "The password is `conquer`.")

    await client.process_commands(message)


@client.event
async def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0.mention} to {1}! Type `!help` to see available commands.'
    await client.send_message(server, fmt.format(member, "OP Ark"))


@client.command()
async def joined(member: discord.Member):
    """Says when a member joined."""
    await client.say('{0.name} joined on {0.joined_at}'.format(member))


@client.command(pass_context=True)
async def wl(member, id64):
    """Adds one or more users to the whitelist"""
    print("User invoking whitelist command: " + member.message.author.name)
    print("Whitelist request: " + id64)

    if rolecheck(member.message.author) is True:
        ids = [y for y in (x.strip() for x in member.message.content.replace(
            "!wl ", "").splitlines()) if y]
        print(ids)
        validation = re.compile(r"(?!76561197960287930)\d{17}")
        for request in ids:
            if validation.fullmatch(request) is not None:
                whitelist_paths = [
                    r"C:\Users\Administrator\Desktop\Ark\Ark Server Manager Data Directory\Servers\Server3\ShooterGame\Binaries\Win64\PlayersExclusiveJoinList.txt"]
                status = 0
                for path in whitelist_paths:
                    whitelist = [line.rstrip('\n') for line in open(path)]

                    if request in whitelist:
                        await client.say("Player is already whitelisted.")
                        break
                    else:
                        try:
                            with open(path, "a") as myfile:
                                myfile.write(request + "\n")
                            status = 1
                            print("path")
                        except:
                            await client.say("Unable to whitelist this player.")
                            break
                if status == 1:
                    await client.say("Player has been whitelisted.")

            elif request == "76561197960287930":
                await client.say("That's the example ID from steamid.io. Not only has this player not been whitelisted but you have brought great shame to your family. Dishonor on you. Dishonor on your cow.")
            else:
                await client.say("Invalid SteamID64. Please verify this SteamID64 is correct on https://steamid.io/lookup.")
    else:
        await client.say("You have no power here!")


@client.command(pass_context=True)
async def wlcheck(member, id64):
    """Adds one or more users to the whitelist"""
    whitelist = [r"C:\Users\Administrator\Desktop\Ark\Ark Server Manager Data Directory\Servers\Server3\ShooterGame\Binaries\Win64\PlayersExclusiveJoinList.txt"]
    if id64 in [line.rstrip('\n') for line in open(whitelist[0])]:
        await client.say(id64 + " is currently on the whitelist.")
    else:
        await client.say(id64 + " is not on the whitelist.")

@client.command()
async def servertime():
    """Show the current time on the server"""
    await client.say("It is " + datetime.datetime.now().strftime("%I:%M %p PST") + ".")


@client.command(pass_context=True)
async def mtg(message):
    """link a mtg card"""
    try:
        await client.say(mtg_card_link(message.message.content[5:]))
    except Exception as err:
        await client.say(err)


@client.command()
async def join():
    """Provides server connection links"""
    await client.say("<:rex:274395290214072321> Join Conquer the Ark: steam://connect/73.118.210.163:27015/")


@client.command()
async def minecraft():
    """Show the current time on the server"""
    try:
        mc_playerlist = MinecraftServer(
            "objectivelyperfect.com").query().players.names
        if mc_playerlist == []:
            await client.say("No one is playing Minecraft.")
        else:
            await client.say("The following player(s) are online: " + ", ".join(mc_playerlist))
    except Exception as e:
        print("Minecraft error:", e)
        await client.say("Something broke! Tell Failoe.")


@client.group(pass_context=True)
async def rates(message):
    """Shows notable server rates."""
    rates_msg = """```OP-CTA uses vanilla "Evolution Event" settings.```"""
    if message.invoked_subcommand is None:
        await client.send_message(message.message.author, rates_msg)


@client.command()
async def beacon(color=None):
    """Returns sample beacon loot."""
    randint = random.randrange(3) + 1
    randitem = random.choice(["Water Jar Blueprint",
                              "Compass Blueprint",
                              "Medium Crop Plot Blueprint"])
    msg = "Your loot is " + str(randint) + " " + \
        randitem + ("s!" if randint > 1 else "!")
    await client.say(msg)


@client.group(pass_context=True)
async def online(ctx):
    """Shows online players. Usage: !online island|scorched"""
    if ctx.invoked_subcommand is None:
        await client.send_message(ctx.message.author, steamplayers("objectivelyperfect.com", 27015))

client.run(open('private.txt').read())
