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


@client.command(pass_context=True)
async def tameinfo(ctx):
    message_split = ctx.message.content.split(" ")
    dino = message_split[1].lower()
    level = message_split[2]
    url = "http://www.dododex.com/taming/{}/{}?taming=2".format(dino, level)

    page = requests.get(url)
    if page.status_code != 200:
        await client.send_message(ctx.message.channel, "Unable to find \"{}\". Check your spelling and format. Ex: `!tameinfo rex 120`".format(dino))
        return
    soup = BeautifulSoup(page.content, "html5lib")

    dino_img = soup.find('img', {'id': 'mainImage'})['src']

    taming_table = soup.find('table', {'class': 'tamingTable'})

    em = discord.Embed(title='__**{}**__'.format(dino.title()), description='**Level {}**'.format(level), colour=0xDEADBF)

    for food_row in taming_table.tbody.find_all('tr')[1:]:

        row_list = food_row.find_all('td')
        food_name = row_list[0].text
        food_quantity = row_list[1].text
        food_time = row_list[2].text
        narcs = food_row.find('img', {'src': '/media/item/Narcotics.png'}).parent
        narcs.div.decompose()
        narcs = narcs.text.strip()

        em.add_field(name=food_name, value="Qty: {}, Time: {}, Narcs: {}".format(food_quantity, food_time, narcs), inline=False)

    await client.send_message(ctx.message.channel, embed=em)
