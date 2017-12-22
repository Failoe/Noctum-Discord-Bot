#!python3

# import valve.source.a2s
import praw

import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import random
import discord
import asyncio
from discord.ext import commands
import re
import logging
import os
import datetime

from mcstatus import MinecraftServer
from bs4 import BeautifulSoup
import requests

__version__ = 0.2

os.system("title "+"Noctum Bot{}".format(__version__))

# logging.basicConfig(level=logging.INFO)
kibbledict = {"Tapejara" : "Allosaurus Egg","Carno" : "Ankylo Egg","Diplocaulus" : "Archaeopteryx Egg","Spino" : "Argentavis Egg","Sabertooth" : "Bronto Egg","Thorny Dragon" : "Morellatops","Trike" : "Carno Egg","Direbear" : "Carno Egg","Direwolf" : "Carno Egg","Pelagornis" : "Compy Egg","Ankylo" : "Dilo Egg","Doedicurus" : "Dilo Egg","Pachy" : "Dilo Egg","Gallimimus" : "Dimetrodon Egg","Megaloceros" : "Dimorph Egg","Allosaurus" : "Diplo Egg","Pteranodon" : "Dodo Egg","Ichthy" : "Dodo Egg","Mesopithecus" : "Dodo Egg","Terror Bird" : "Gallimimus Egg","Castoroides" : "Gallimimus Egg","Angler" : "Kairuku Egg","Diplodocus" : "Lystro Egg","Rock Elemental" : "Mantis Egg","Megalosaurus" : "Oviraptor Egg","Paracer" : "Pachy Egg","Raptor" : "Parasaur Egg","Archaeopteryx" : "Pelagornis Egg","Carbonemys" : "Pteranodon Egg","Rex" : "Pulmonoscorpius Egg","Beelzebufo" : "Pulmonoscorpius Egg","Mosasaurus" : "Quetzal Egg","Giganotosaurus" : "Quetzal Egg","Dimetrodon" : "Quetzal Egg","Mammoth" : "Raptor Egg","Plesiosaur" : "Rex Egg","Quetzal" : "Rex Egg","Stego" : "Sarco Egg","Megalodon" : "Spino Egg","Argentavis" : "Stego Egg","Kaprosuchus" : "Tapejara Egg","Woolly Rhino" : "Terror Bird Egg","Lymantria" : "Thorny Dragon Egg","Gigantopithecus" : "Titanoboa Egg","Dunkleosteus" : "Titanoboa Egg","Sarco" : "Trike Egg","Bronto" : "Turtle Egg","Morellatops" : "Vulture Egg", "Therizinosaurus" : "Megalosaurus", "Stabby Flap Flap" : "Megalosaurus", "Failoe" : "player's tears", "Majestic Flap Flap" : "Stego", "Scooby" : "beer", "Zeeth" : "salt", "Laylani" : "bears", "Adrien" : "art supplies"}

description = "Noctum bot for OP Ark's Discord"

"""Start of Google Sheets Code"""

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'

def get_gsheets_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    return credentials

credentials = get_gsheets_credentials()
http = credentials.authorize(httplib2.Http())
discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                'version=v4')
service = discovery.build('sheets', 'v4', http=http,
                          discoveryServiceUrl=discoveryUrl)


def mtg_card_link(cardname):
    page = requests.get("http://magiccards.info/query?q={}".format(cardname))
    soup = BeautifulSoup(page.content, 'html5lib')
    image_link = soup.find_all('tbody')[3].img['src']
    if "magiccards.info" not in image_link:
        return "http://magiccards.info{}".format(image_link)
    else:
        return image_link



def gsheets():
    global pending_whitelists
    spreadsheetId = '18HBUAsSuZPOSSGlN17aJ5NbxZxla2imrBjNSm4XOAaw'
    rangeName = 'Form Responses 1!A2:H'
    banRange = 'Banned Players!A1:H'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    ban_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=banRange).execute()

    ban_values = ban_result.get('values',[])

    values = result.get('values', [])
    if not values:
        print('No data found.')
        pending_whitelists = 0

    else:
        # print('Name, Major:')
        for row in values:
            body = {
                    "range": "Processed Applications!A1:G1",
                    "majorDimension": 'ROWS',
                    "values":[row],
                    }
            service.spreadsheets().values().append(spreadsheetId = '18HBUAsSuZPOSSGlN17aJ5NbxZxla2imrBjNSm4XOAaw',
                                                    range="Processed Applications!A1:G1",
                                                    body=body,
                                                    valueInputOption='USER_ENTERED').execute()
        pending_whitelists = 1
    service.spreadsheets().values().clear(spreadsheetId='18HBUAsSuZPOSSGlN17aJ5NbxZxla2imrBjNSm4XOAaw',
                                           range="Form Responses 1!A2:G",
                                           body={"range": "Form Responses 1!A2:G"}
                                            ).execute()
    return values, ban_values

"""End of Google Sheets Code"""

def steamplayers(address="73.109.26.174",port=27015):
    """Returns a string with the list of players for a given server."""    
    SERVER_ADDRESS = (address,port)
    
    server = valve.source.a2s.ServerQuerier(SERVER_ADDRESS)
    info = server.get_info()
    players = server.get_players()
    header =("Online Players:\n")
    
    playerlist = '\n'.join([x['name'] for x in players["players"] if x['name'] != ""])
    
    return "```"+header+playerlist+"```"

def timetilrestart():
    h = int(datetime.datetime.now().strftime("%I"))
    m = int(datetime.datetime.now().strftime("%M"))
    
    decimal_hours = h + m/60
    
    hours = 17 - decimal_hours if decimal_hours >= 5 else 5 - decimal_hours
    
    
    output = (  "The server will restart in approximately " + str(round(hours,2)) +\
                " hours at which point you will be able to connect.")
    
    return output

def redditmessage(user, status):
    try:
        BOT_USERNAME = 'failtest'
        BOT_PASSWORD = 'testpass'
        USERAGENT = 'OPArk Greeting'
        my_client_id = '2at0TMSlxBwXnQ'
        my_client_secret = 'BK9MET6xwrt8Ew0A7N16SLlp6sQ'
        
        r = praw.Reddit(user_agent=USERAGENT,
            client_id=my_client_id,
            client_secret=my_client_secret,
            username=BOT_USERNAME,
            password=BOT_PASSWORD)
        
        clean_user = user[user.rfind("/")+1:]
        
        ttr = timetilrestart()

        exampleID_msg = (   "The id you provided (76561197960287930) is the sample ID provided on "\
                            "[steamid.io](https://steamid.io/lookup). Please visit the web site "\
                            "again and make sure you search for your own ID and either resubmit "\
                            "an application or message one of our admins on "\
                            "[Discord](https://discord.gg/bbEB82D) and we'll resolve this issue. "\
                            "Example [Steam ID Lookup](https://steamid.io/lookup/76561197960287930)"\
                            "\n\nThanks,\n\nFailoe - Server Admin\n\n(This is an automated message "\
                            " from Noctum-bot, please do not reply to this message as no one but "\
                            " the void will see it. Our admins can be reached via "\
                            " [reddit](https://www.reddit.com/message/compose?to=%2Fr%2Fopark). "\
                            " For a quicker response, please contact us on our "\
                            " [Discord server](https://discord.gg/bbEB82D).")
        
        banned_msg = ("If you have received this messasge, your Steam ID is on our " \
                    "banlist. If you believe you are receiving this message in " \
                    "error please contact us via " \
                    "[reddit](https://www.reddit.com/message/compose?to=%2Fr%2Fopark)." \
                    "\n\nFailoe - Server Admin")
    
        accepted_msg = ("Your whitelist application has been accepted for OP Ark!  "\
                    + ttr +\
                    " If you haven't joined already, we would be happy "\
                    "to have you join us on [Discord](https://discord.gg/bbEB82D). "\
                    "We use Discord to organize server events, provide admin "\
                    "support, and hang out as a community.  If you have any issues "\
                    "please be sure to find an admin so we can help you out as "\
                    "soon as possible.\n\nWelcome to the party,\n\nFailoe - "\
                    "Server Admin\n\n"\
                    "(This is an automated message from Noctum-bot, please do not "\
                    "reply to this message as no one but the void will see it. Our "\
                    "admins can be reached via [reddit](https://www.reddit.com/message/"\
                    "compose?to=%2Fr%2Fopark). For a quicker response, please "\
                    "contact us on our [Discord server](https://discord.gg/bbEB82D).)")
        
        alreadywhitelisted_msg = ("If you are seeing this message you have already been "\
                    "accepted on OP Ark's whitelist and a second application"\
                    "has been discarded. If you believe you received this "\
                    "message in error please contact us via " \
                    "[reddit](https://www.reddit.com/message/compose?to=%2Fr%2Fopark)." \
                    "\n\nFailoe - Server Admin")

        if status == "exampleID":
            body = exampleID_msg
        elif status == "banned":
            body = banned_msg
        elif status == "accepted":
            body = accepted_msg
        elif status == "already":
            body = alreadywhitelisted_msg

        try:
            rrecipient = r.redditor(clean_user)
            rrecipient.message("OP Ark Whitelist", body)
            print("Reddit messaged user:", clean_user)
        except ValueError:
            print("Unable to message user:", clean_user)
    except Exception as e:
        print("Error sending reddit message:", e)

client = commands.Bot(command_prefix=['!'], description=description)


def rolecheck(member):
    """Returns whether or not a user has the Ark Admin role."""
    rolelist = []
    for role in member.roles:
        rolelist.append(role.name)
    if 'Admin' in rolelist or 'Mod' in rolelist:
        return True
    else:
        return False

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print(client)
    await client.change_presence(game=discord.Game(name='god'))

@client.event
async def on_message(message):
    print(datetime.datetime.now().time(), message.channel, message.author.name, "|", message.content)
    # if str(message.channel) == "coding-lair" or str(message.channel) == "bot":
    if message.author.id != "260964776945909760":
        if message.content.lower().startswith("noctum") and "kibble" in message.content.lower():
            for dino_name in kibbledict.keys():
                if dino_name.lower() in message.content.lower():
                    msg = "The favorite kibble of the "+dino_name+" is "+kibbledict[dino_name]+"."
                    await client.send_message(message.channel, msg)

        elif message.content.startswith('Noctum help') or message.content == ("help"):
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
async def joined(member : discord.Member):
    """Says when a member joined."""
    await client.say('{0.name} joined on {0.joined_at}'.format(member))

@client.command(pass_context=True)
async def wl(member, id64):
    """Adds one or more users to the whitelist"""
    print("User invoking whitelist command: " + member.message.author.name)
    print("Whitelist request: " + id64)

    if rolecheck(member.message.author) == True:
        ids = [y for y in (x.strip() for x in member.message.content.replace("!wl ","").splitlines()) if y]
        print(ids)
        validation = re.compile(r"(?!76561197960287930)\d{17}")
        for request in ids:
            if validation.fullmatch(request) != None:
                whitelist_paths = [r"C:\Users\Administrator\Desktop\Ark\Ark Server Manager Data Directory\Servers\Server3\ShooterGame\Binaries\Win64\PlayersExclusiveJoinList.txt"]
                status = 0
                for path in whitelist_paths:
                    whitelist = [line.rstrip('\n') for line in open(path)]
        
                    if request in whitelist:
                        await client.say("Player is already whitelisted.")
                        break
                    else:
                        try:
                            with open(path, "a") as myfile:
                                myfile.write(request+"\n")
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
    whitelist = ["C:/Users/Administrator/Desktop/Ark/Ark Server Manager Data Directory/Servers/OP Island/ShooterGame/Binaries/Win64/PlayersExclusiveJoinList.txt","C:/Users/Administrator/Desktop/Ark/Ark Server Manager Data Directory/Servers/OP Scorched/ShooterGame/Binaries/Win64/PlayersExclusiveJoinList.txt"]
    if id64 in [line.rstrip('\n') for line in open(whitelist[0])]:
        await client.say(id64 + " is currently on the Island whitelist.")
    else:
        await client.say(id64 + " is not on the Island whitelist.")

    if id64 in [line.rstrip('\n') for line in open(whitelist[1])]:
        await client.say(id64 + " is currently on the Scorched whitelist.")
    else:
        await client.say(id64 + " is not on the Scorched whitelist.")

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
    # await client.say("<:rex:274395290214072321> Join The Island: steam://connect/73.118.210.163:27015/" \
    #     "\n<:wyvern:274395277543079936> Join Scorched Earth: steam://connect/73.118.210.163:27017/")

@client.command()
async def minecraft():
    """Show the current time on the server"""
    # await client.say("<:minecraft:274092717452034048> Connect to the server via tabloidgamer.com <:MC_Heart:274381867044569088> ")
    try:
        mc_playerlist = MinecraftServer("objectivelyperfect.com").query().players.names
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
    rates_msg = """```OP Ark Rates and Major Server Changes

2.5x taming
1.5x exp
1.6x gathering

15x maturation
1x mating
8x incubation

2x Longer Item/Corpse Decomposition Time
2x Egg Laying Frequency
4x Platform Structure Limit

Auto Save Interval: 15 minutes
Max Dino Level: 120
Mods: None
Disabled Animals: Titanosaur, Quetzalcoatlus, Giganotosaurus

Use '!rates all' for complete list of settings.```
"""
    if message.invoked_subcommand is None:
        await client.send_message(message.message.author, rates_msg)

@rates.command(pass_context=True, name='all')
async def _client(message):
    """Shows all the config options."""

    pass

@client.command(pass_context=True)
async def whitelist(ctx):
    """Processes all pending whitelist applications"""
    if rolecheck(ctx.message.author) == True:
        initial_msg = await client.say("Processing whitelist requests...")
        validation = re.compile(r"(?!76561197960287930)\d{17}")
        ids, banlist = gsheets()
        
        banned_ids = []
        for x in banlist:
            banned_ids.append(x[1])

        for request in ids:
            try:
                if validation.fullmatch(request[1]) != None and request[1] not in banned_ids:
                    whitelist_paths = ["C:/Users/Administrator/Desktop/Ark/Ark Server Manager Data Directory/Servers/OP Island/ShooterGame/Binaries/Win64/PlayersExclusiveJoinList.txt","C:/Users/Administrator/Desktop/Ark/Ark Server Manager Data Directory/Servers/OP Scorched/ShooterGame/Binaries/Win64/PlayersExclusiveJoinList.txt"]
                    status = 0
                    for path in whitelist_paths:
                        whitelist = [line.rstrip('\n') for line in open(path)]
            
                        if request[1] in whitelist:
                            await client.say(request[2] + " is already whitelisted.")
                            reddit = "already"
                            break
                        else:
                            try:
                                with open(path, "a") as myfile:
                                    myfile.write(request[1]+"\n")
                                status = 1
                            except:
                                await client.say("Unable to whitelist "+ request[2] + ". Possible error.")
                                break
                    if status == 1:
                        await client.say(request[2] + " has been whitelisted.")
                        reddit = "accepted"
                elif request[1] in banned_ids:
                    await client.say(request[2] + " is on the banlist and will not be whitelisted.")
                    reddit = "banned"
                elif request[1] == "76561197960287930":
                    await client.say(request[2] + " provided the example ID. They are not whitelisted.")
                    reddit = "exampleID"
                else:
                    await client.say("Invalid SteamID64 from " + request[2])
                redditmessage(request[3],reddit)
            except Exception as e:
                print("Error: " + str(e))
        if pending_whitelists == 0:
            await client.edit_message(initial_msg, "No pending whitelist requests.")
        else:
            await client.delete_message(initial_msg)
    else:
        await client.say("Do not test me " + ctx.message.author.name + ".")

@client.command()
async def beacon(color=None):
    """Returns sample beacon loot."""
    randint = random.randrange(3)+1
    randitem = random.choice(   ["Water Jar Blueprint",
                                "Compass Blueprint",
                                "Medium Crop Plot Blueprint"])
    msg = "Your loot is " + str(randint) + " " + randitem + ("s!" if randint > 1 else "!")
    await client.say(msg)

@client.group(pass_context=True)
async def online(ctx):
    """Shows online players. Usage: !online island|scorched"""
    if ctx.invoked_subcommand is None:
        await client.send_message(ctx.message.author, steamplayers("objectivelyperfect.com", 27015))

client.run(open('private.txt').read())