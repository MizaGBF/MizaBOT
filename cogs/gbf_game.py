import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import math
import string

class GBF_Game(commands.Cog):
    """GBF-themed Game commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xfce746

    # used by the gacha games
    def getRoll(self, ssr, sr_mode = False):
        d = random.randint(1, 10000)
        if d < ssr: return 0
        elif (not sr_mode and d < 1500 + ssr) or sr_mode: return 1
        return 2

    legfestWord = {"double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2"}
    notfestWord = {"normal", "x1", "3%", "gacha", "1"}
    def isLegfest(self, word):
        word = word.lower()
        if word not in self.notfestWord and (word in self.legfestWord or self.bot.gbfdata.get('gachacontent', '').find("**Premium Gala**") != -1): return 2 # 2 because the rates are doubled
        return 1

    def tenDraws(self, rate, draw, mode = 0):
        result = [0, 0, 0]
        x = 0
        while mode > 0 or (mode == 0 and x < draw):
            i = 0
            while i < 10:
                r = self.getRoll(rate, i == 9)
                result[r] += 1
                i += 1
            if mode == 1 and result[0] > 0: break # gachapin / mukku
            elif mode == 2 and result[0] >= 5: break # super mukku
            x += 1
        return result

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(60, 60, commands.BucketType.guild)
    async def single(self, ctx, double : str = ""):
        """Do a single roll
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        r = self.getRoll(300*l)

        if r == 0: msg = "Luckshitter! It's a {}".format(self.bot.getEmote('SSR'))
        elif r == 1: msg = "It's a {}".format(self.bot.getEmote('SR'))
        else: msg = "It's a {}, too bad!".format(self.bot.getEmote('R'))

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} did a single roll".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(25)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def ten(self, ctx, double : str = ""):
        """Do ten gacha rolls
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        msg = ""
        i = 0
        while i < 10:
            r = self.getRoll(300*l, i == 9)
            if i == 5: msg += '\n'
            if r == 0: msg += '{}'.format(self.bot.getEmote('SSR'))
            elif r == 1: msg += '{}'.format(self.bot.getEmote('SR'))
            else: msg += '{}'.format(self.bot.getEmote('R'))
            i += 1

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} did ten rolls".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(25)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def spark(self, ctx, double : str = ""):
        """Do thirty times ten gacha rolls
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        result = self.tenDraws(300*l, 30)
        msg = "{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/300)

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} sparked".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(25)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['frenzy'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def gachapin(self, ctx, double : str = ""):
        """Do ten rolls until you get a ssr
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        result = self.tenDraws(300*l, 0, 1)
        count = result[0]+result[1]+result[2]
        msg = "Gachapin stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Gachapin".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(25)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mook'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def mukku(self, ctx, super : str = ""):
        """Do ten rolls until you get a ssr, 9% ssr rate
        You can add "super" for a 9% rate and 5 ssr mukku"""
        if super.lower() == "super":
            footer = "Super Mukku ▫️ 15% SSR Rate and at least 5 SSRs"
            result = self.tenDraws(1500, 0, 2)
        else:
            footer = "9% SSR rate"
            result = self.tenDraws(900, 0, 1)
        count = result[0]+result[1]+result[2]
        msg = "Mukku stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Mukku".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(25)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['scratcher'])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def scratch(self, ctx):
        """Imitate the GBF scratch game from Anniversary 2020"""
        # loot table (based on real one)
        loot = {
            'Siero Ticket':10,
            'Sunlight Stone':300,
            'Gold Brick':200,
            'Damascus Ingot':450,
            'Agni':1302, 'Varuna':1302, 'Titan':1302, 'Zephyrus':1302, 'Zeus':1302, 'Hades':1302, 'Shiva':1302, 'Europa':1302, 'Godsworn Alexiel':1302, 'Grimnir':1302, 'Lucifer':1302, 'Bahamut':1302, 'Michael':1302, 'Gabriel':1302, 'Uriel':1302, 'Raphael':1302, 'Metatron':1302, 'Sariel':1302, 'Belial':1302, # (18*1375)->24750 / 19
            'Murgleis':862, 'Benedia':862, 'Gambanteinn':862, 'Love Eternal':862, 'AK-4A':862, 'Reunion':862, 'Ichigo-Hitofuri':862, 'Taisai Spirit Bow':862, 'Unheil':862, 'Sky Ace':862, 'Ivory Ark':862, 'Blutgang':862, 'Eden':862, 'Parazonium':862, 'Ixaba':862, 'Blue Sphere':862, 'Certificus':862, 'Fallen Sword':862, 'Mirror-Blade Shard':862, 'Galilei\'s Insight':862, 'Purifying Thunderbolt':862, 'Vortex of the Void':862, 'Sacred Standard':862, 'Bab-el-Mandeb':862, 'Cute Ribbon':862, 'Kerak': 862, 'Sunya':862, 'Fist of Destruction': 862, 'Yahata\'s Naginata': 862, # (25x1000)->25000 / 29
            'Crystals x3000':8000,
            'Intricacy Ring':3000, 'Gold Spellbook':3000, 'Moonlight Stone':3000, 'Gold Moon x2':3000, 'Ultima Unit x3':3000, 'Silver Centrum x5':3000, 'Primeval Horn x3':3000, 'Horn of Bahamut x4':3000, 'Legendary Merit x5':3000, 'Steel Brick':3000,
            'Lineage Ring x2':4000, 'Coronation Ring x3':4000, 'Silver Moon x5':4000, 'Bronze Moon x10':5000, 'Half Elixir x100':6000, 'Soul Berry x300':6000
        }
        message = None # store the message to edit
        mm = 0 # maximum random loot value
        for x in loot:
            mm += loot[x] # calculated here

        # select the loot
        selected = {}
        sm = random.randint(4, 6) # number of loots, 4 to 6 max
        i = 0
        while i < sm:
            if len(selected) == 1 and n > 20000: n = random.randint(0, mm//10) # add one rarer loot
            else: n = random.randint(0, mm-1) # roll a dice
            c = 0
            check = "" # check which loot match in this loop
            for x in loot:
                if n < c + loot[x]:
                    check = x
                    break
                else:
                    c += loot[x]
            if check != "" and check not in selected: # add to the list if correct
                selected[check] = 0
                i += 1

        # build the scratch grid
        hidden = "[???????????????]"
        grid = []
        win = ""
        keys = list(selected.keys())
        for x in keys: # add all our loots once
            grid.append([x, False])
            selected[x] = 1
        # add the first one twice (it's the winning one)
        grid.append([keys[0], False])
        grid.append([keys[0], False])
        selected[keys[0]] = 3
        win = keys[0]
        nofinal = False
        while len(grid) < 10: # fill the grid up to TEN times
            n = random.randint(1, len(keys)-1)
            if selected[keys[n]] < 2:
                grid.append([keys[n], False])
                selected[keys[n]] += 1
            elif len(grid) == 9: # 10 means final scratch so we stop at 9 and raise a flag if the chance arises
                grid.append(['', False])
                nofinal = True
                break
        while True: # shuffle the grid until we get a valid one
            random.shuffle(grid)
            if nofinal and grid[-1][0] == "": break
            elif not nofinal and grid[-1][0] == keys[0]:
                win = ""
                break

        # play the game
        win_flag = False
        reveal_count = 0
        fields = [{'name': "{}".format(self.bot.getEmote('1')), 'value':''}, {'name': "{}".format(self.bot.getEmote('2')), 'value':''}, {'name': "{}".format(self.bot.getEmote('3')), 'value':''}]
        pulled = {}
        msg = ""
        # main loop
        while True:
            # print the grid
            for i in range(0, 9):
                if i < 3: fields[i]['value'] = ''
                if grid[i][1] == False: fields[i%3]['value'] += "{}\n".format(hidden)
                else:
                    c = pulled[grid[i][0]]
                    if c == 3: fields[i%3]['value'] += "**{}**\n".format(grid[i][0])
                    elif c == 2: fields[i%3]['value'] += "__{}__\n".format(grid[i][0])
                    else: fields[i%3]['value'] += "{}\n".format(grid[i][0])
            # send the message
            if message is None:
                message = await ctx.send(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            else:
                await message.edit(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            await asyncio.sleep(1)
            # win sequence
            if win_flag:
                if win == "": # final scratch must happens
                    win = grid[-1][0]
                    msg += "*The Final scratch...*\n"
                    await message.edit(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, fields=fields, color=self.color))
                    await asyncio.sleep(2)
                msg += ":confetti_ball: :tada: **{}** :tada: :confetti_ball:".format(win)
                for i in range(0, 9): # update the grid
                    if i < 3: fields[i%3]['value'] = ''
                    c = pulled.get(grid[i][0], 0)
                    if grid[i][1] == False: fields[i%3]['value'] += "~~{}~~\n".format(grid[i][0])
                    elif c == 3: fields[i%3]['value'] += "**{}**\n".format(grid[i][0])
                    elif c == 2: fields[i%3]['value'] += "__{}__\n".format(grid[i][0])
                    else: fields[i%3]['value'] += "{}\n".format(grid[i][0])
                await message.edit(embed=self.bot.buildEmbed(author={'name':"{} scratched".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, fields=fields, color=self.color))
                if not self.bot.isAuthorized(ctx):
                    await asyncio.sleep(30)
                    await message.delete()
                    await self.bot.react(ctx.message, '✅') # white check mark
                return
            # next pull
            i = random.randint(0, 8)
            while grid[i][1] == True:
                i = random.randint(0, 8)
            grid[i][1] = True
            reveal_count += 1
            selected[grid[i][0]] -= 1
            pulled[grid[i][0]] = pulled.get(grid[i][0], 0) + 1
            if reveal_count == 9 or (selected[grid[i][0]] == 0 and grid[i][0] == win):
                win_flag = True

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['chests', 'rush'])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def chest(self, ctx):
        """Imitate the GBF treasure game from Summer 2020"""
        message = None
        loot = {
            'Murgleis':150, 'Benedia':150, 'Gambanteinn':150, 'Love Eternal':150, 'AK-4A':150, 'Reunion':150, 'Ichigo-Hitofuri':150, 'Taisai Spirit Bow':150, 'Unheil':150, 'Sky Ace':150, 'Ivory Ark':150, 'Blutgang':150, 'Eden':150, 'Parazonium':150, 'Ixaba':150, 'Blue Sphere':150, 'Certificus':150, 'Fallen Sword':150, 'Mirror-Blade Shard':150, 'Galilei\'s Insight':150, 'Purifying Thunderbolt':150, 'Vortex of the Void':150, 'Sacred Standard':150, 'Bab-el-Mandeb':150, 'Cute Ribbon':150, 'Kerak':150, 'Sunya':150, 'Fist of Destruction':150, 'Yahata\'s Naginata':150,
            'Ruler of Fate':150, 'Ancient Bandages':150, 'Gottfried':150, 'Acid Bolt Shooter':150, 'Mystic Spray Gun':150, 'Metal Destroyer':150, 'Gangsta Knife':150, 'Vagabond':150, 'Heavenly Fawn Bow':150, 'Another Sky':150,
            'Agni':150, 'Varuna':150, 'Titan':150, 'Zephyrus':150, 'Zeus':150, 'Hades':150, 'Shiva':150, 'Europa':150, 'Godsworn Alexiel':150, 'Grimnir':150, 'Lucifer':150, 'Bahamut':150, 'Michael':150, 'Gabriel':150, 'Uriel':150, 'Raphael':150, 'Metatron':150, 'Sariel':150, 'Belial':150,
            '10K Crystal':100,
            '3K Crystal':400,'Intricacy Ring x3':400,'Damascus Crystal x3':400, 'Premium 10-Part Ticket':400,
            'Intricacy Ring':500, 'Lineage Ring x2':500, 'Coronation Ring x3':500, 'Gold Moon x2':500,
            'Gold Moon':800, 'Silver Moon x5':800, 'Bronze Moon x10':800, 'Premium Draw Ticket':800, 'Gold Spellbook x3':800,
            'Half Elixir x10':1000, 'Soul Berry x10':1000, 
            "Satin Feather x10":1250, "Zephyr Feather x10":1250, "Untamed Flame x10":1250, "Rough Stone x10":1250, "Fresh Water Jug x10":1250, "Swirling Amber x10":1250, "Falcon Feather x10":1250, "Vermilion Stone x10":1250, "Hollow Soul x10":1250, "Lacrimosa x10":1250, "Foreboding Clover x10":1250, "Blood Amber x10":1250, "Antique Cloth x10":1250, 
            "White Dragon Scale x10":1250, "Champion Merit x10":1250, "Supreme Merit x10":1250, "Blue Sky Crystal x10":1250, "Rainbow Prism x10":1250, "Rubeus Centrum x10":1250, "Indicus Centrum x10":1250, "Luteus Centrum x10":1250, "Galbinus Centrum x10":1250, "Niveus Centrum x10":1250, "Ater Centrum x10":1250, "Fire Urn x10":1250, "Water Urn x10":1250, "Earth Urn x10":1250, "Wind Urn x10":1250, "Light Urn x10":1250, "Dark Urn x10":1250, "Horn of Bahamut x10":1250, "Primeval Horn x10":1250, "Legendary Merit":1250, 
            "Sword Stone x50":1000, "Dagger Stone x50":1000, "Spear Stone x50":1000, "Axe Stone x50":1000, "Staff Stone x50":1000, "Pistol Stone x50":1000, "Melee Stone x50":1000, "Bow Stone x50":1000, "Harp Stone x50":1000, "Katana Stone x50":1000, "Silver Centrum x5":1000, "Ultima Unit x3":1000, "Fire Quartz x50":1000, "Water Quartz x50":1000, "Earth Quartz x50":1000, "Wind Quartz x50":1000, "Light Quartz x50":1000, "Dark Quartz x50":1000, "Shiva Omega Anima x3":1000, "Europa Omega Anima x3":1000, "Alexiel Omega Anima x3":1000, "Grimnir Omega Anima x3":1000, "Metatron Omega Anima x3":1000, "Avatar Omega Anima x3":1000
        }

        mm = 0 # maximum random loot value
        rm = 0 # rare loot value
        for x in loot:
            mm += loot[x] # calculated here
            if x == 'Premium 10-Part Ticket': rm = mm

        results = []
        l = random.randint(0, 9)
        while len(results) < l:
            n = random.randint(1, mm)
            c = 0
            check = ""
            for x in loot:
                if n < c + loot[x]:
                    check = x
                    break
                else:
                    c += loot[x]
            if check != "":
                if n < rm and len(results) == l - 1: results.append(["**" + check + "**", -1])
                else: results.append([check, 0])

        while len(results) < 9: results.append([None, 0])
        random.shuffle(results)

        opened = 0
        game_over = False
        display_chest = True
        fields = [{'name': "{}".format(self.bot.getEmote('1')), 'value':''}, {'name': "{}".format(self.bot.getEmote('2')), 'value':''}, {'name': "{}".format(self.bot.getEmote('3')), 'value':''}]
        title = "{} is opening...".format(ctx.author.display_name)
        while True:
            for i in range(9):
                if i < 3: fields[i]['value'] = ''
                if results[i][1] == -3: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.getEmote('red'))
                elif results[i][1] == -2: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.getEmote('kmr'))
                elif results[i][1] <= 0 and display_chest: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.getEmote('gold'))
                elif results[i][1] <= 0: fields[i%3]['value'] += "✖️\n"
                elif results[i][0] is None: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.getEmote('kmr'))
                else: fields[i%3]['value'] += results[i][0] + "\n"

            if game_over:
                title = "{} opened".format(ctx.author.display_name)
            if message is None:
                message = await ctx.send(embed=self.bot.buildEmbed(author={'name':title, 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            else:
                await message.edit(embed=self.bot.buildEmbed(author={'name':title, 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            if game_over:
                if not self.bot.isAuthorized(ctx):
                    await asyncio.sleep(45)
                    await message.delete()
                    await self.bot.react(ctx.message, '✅') # white check mark
                return
            await asyncio.sleep(1)

            while True:
                n = random.randint(0, 8)
                if results[n][1] <= 0:
                    if results[n][1] == -3:
                        results[n][1] = 1
                        opened += 1
                        game_over = True
                        break
                    elif results[n][1] < 0:
                        if l == opened + 1:
                            results[n][1] -= 1
                            display_chest = False
                            break
                    elif results[n][0] is None:
                        if l == opened:
                            results[n][1] = 1
                            game_over = True
                            display_chest = False
                            break
                    else:
                        results[n][1] = 1
                        opened += 1
                        if opened == 9:
                            game_over = True
                            display_chest = False
                        break

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def roulette(self, ctx, double : str = ""):
        """Imitate the GBF roulette
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        mode = 0
        roll = 0
        rps = ['rock', 'paper', 'scissor']
        d = random.randint(1, 36000)
        ct = self.bot.getJST()
        # customization settings
        fix200S = ct.replace(year=2020, month=3, day=29, hour=18, minute=0, second=0, microsecond=0)
        fix200E = fix200S.replace(day=31, hour=5)
        forced3pc = False
        forcedRollCount = 100
        enable200 = False
        enableJanken = False
        if ct >= fix200S and ct < fix200E:
            msg = "{} {} :confetti_ball: :tada: Guaranteed **{} 0 0** R O L L S :tada: :confetti_ball: {} {}".format(self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), forcedRollCount//100, self.bot.getEmote('crystal'), self.bot.getEmote('crystal'))
            roll = forcedRollCount // 10
            d = 0
            if l == 2 and forced3pc:
                footer = "3% SSR rate ▪️ You won't get legfest rates, you fool"
                l = 1
            mode = 3
        elif enable200 and d < 300:
            msg = "{} {} :confetti_ball: :tada: **2 0 0 R O L L S** :tada: :confetti_ball: {} {}".format(self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'))
            roll = 20
        elif d < 1500:
            msg = "**Gachapin Frenzy** :four_leaf_clover:"
            mode = 1
        elif d < 2000:
            msg = ":confetti_ball: :tada: **100** rolls!! :tada: :confetti_ball:"
            roll = 10
        elif d < 6200:
            msg = "**30** rolls! :clap:"
            roll = 3
        elif d < 18000:
            msg = "**20** rolls :open_mouth:"
            roll = 2
        else:
            msg = "**10** rolls :pensive:"
            roll = 1
        # janken
        if enableJanken and d >= 2000 and random.randint(0, 2) > 0:
            a = 0
            b = 0
            while a == b:
                a = random.randint(0, 2)
                b = random.randint(0, 2)
            msg += "\nYou got **{}**, Gachapin got **{}**".format(rps[a], rps[b])
            if (a == 1 and b == 0) or (a == 2 and b == 1) or (a == 0 and b == 2):
                msg += " :thumbsup:\nYou **won** rock paper scissor, your rolls are **doubled** :confetti_ball:"
                roll = roll * 2
            else:
                msg += " :pensive:"
        # rolls
        if mode == 0 or mode == 3:
            result = self.tenDraws(300*l, roll)
            msg += "\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/(roll*10))
        elif mode == 1:
            result = self.tenDraws(300*l, 0, 1)
            count = result[0]+result[1]+result[2]
            msg += "\nGachapin stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)
            if count == 10 and random.randint(1, 100) < 99: mode = 2
            elif count == 20 and random.randint(1, 100) < 60: mode = 2
            elif count == 30 and random.randint(1, 100) < 30: mode = 2

        if mode == 2:
            result = self.tenDraws(900, 0, 1)
            count = result[0]+result[1]+result[2]
            msg += "\n:confetti_ball: Mukku stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        if mode == 3:
            result = self.tenDraws(1500, 0, 2)
            count = result[0]+result[1]+result[2]
            msg += "\n:confetti_ball: :confetti_ball: **Super Mukku** stopped after **{}** rolls :confetti_ball: :confetti_ball:\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        final_msg = await ctx.send(embed=self.bot.buildEmbed(author={'name':"{} spun the Roulette".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(30)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def quota(self, ctx):
        """Give you your GW quota for the day"""
        if ctx.author.id in self.bot.ids.get('branded', []):
            await ctx.send(embed=self.bot.buildEmbed(title="{} {} is a bad boy".format(self.bot.getEmote('gw'), ctx.author.display_name), description="Your account is **restricted.**", thumbnail=ctx.author.avatar_url, color=self.color))
            return

        h = random.randint(800, 4000)
        m = random.randint(70, 180)
        c = random.randint(1, 100)

        if ctx.author.id == self.bot.ids.get('wawi', -1):
            c = 7

        if c <= 2:
            c = random.randint(1, 110)
            if c == 1:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got the **Eternal Battlefield Pass** 🤖\nCongratulations!!!\nYou will now revive GW over and ovḛ̸̛̠͕̑̋͌̄̎̍͆̆͑̿͌̇̇̕r̸̛̗̥͆͂̒̀̈́͑̑̊͐̉̎̚̚͝ ̵̨̛͔͎͍̞̰̠́͛̒̊̊̀̃͘ư̷͎̤̥̜̘͈̪̬̅̑͂̂̀̃̀̃̅̊̏̎̚͜͝ͅņ̴̢̛̛̥̮͖͉̻̩͍̱̓̽̂̂͌́̃t̵̞̦̿͐̌͗͑̀͛̇̚͝͝ỉ̵͉͕̙͔̯̯͓̘̬̫͚̬̮̪͋̉͆̎̈́́͛̕͘̚͠ͅļ̸̧̨̛͖̹͕̭̝͉̣̜͉̘͙̪͙͔͔̫̟̹̞̪̦̼̻̘͙̮͕̜̼͉̦̜̰̙̬͎͚̝̩̥̪̖͇̖̲̣͎̖̤̥͖͇̟͎̿̊͗̿̈̊͗̆̈́͋͊̔͂̏̍̔̒̐͋̄̐̄̅̇͐̊̈́̐͛͑̌͛̔͗̈́͌̀͑̌̅̉́̔̇́̆̉͆̄̂͂̃̿̏̈͛̇̒͆͗̈́̀̃̕̕͘̚̚͘͘͠͠͠͝͝͠͝͝ͅͅ ̴̢̛̛̛̯̫̯͕̙͙͇͕͕̪̩̗̤̗̺̩̬̞̞͉̱̊̽̇̉̏̃̑̋̋̌̎̾́̉́͌̿̐̆̒̾̆͒͛͌́͒̄͗͊͑̈́̑̐̂̿̋̊͊̈́̃̋̀̀̈̏̅̍̈͆̊̋͋̀̽͑̉̈́͘͘̕̕͝y̷̧̧̨̢̧̮̭̝̦͙͈͉̜͈̳̰̯͔͓̘͚̳̭͎̳̯͈͓̣͕͙̳̭̱͍͎͖̋͊̀͋͘͘ơ̸̢̗̖̹̹͖̣̫̝̞̦̘̙̭̮͕̘̱̆͋̓͗̾͐̉̏̀͂̄̎̂̈́͌͑̅̆̉̈̒͆̈̈̊͐̔̓̀̿̓̈́͝͝͝͠͝u̶̡̧̡̧̨̧̡̡̢̢̢̪̯͙͍̱̦̠̗̹̼̠̳̣͉̞̩̹͕̫͔͚̬̭̗̳̗̫̥̞̰̘̖̞̤͖̳̮̙͎͎̗̙̳͙͖͓̪̱̞͖̠̣̮̘͍̱̥̹͎͎̦̬̹̼̜͕͙͖̫̝̰̯̜̹̬̯͚͕̰̪̼͓̞̫̖̘͙̞͖̺̩͓̹̘̙̫̩̲̻̪̠̞̺͚̫̰̠̼̖̬͔̗̮͙̱̬̩̮̟͓̫̭̲̘̤͎̱̓̊̇́̀̏̏̾̀̄̆̒̂͐̌͂̈̂̓͋̌̓͘̕̕̚͜͜͜͝ͅͅͅͅŗ̷̡̧̨̢̢̢̧̡̡̧̡̢̧̨̨̡̧̛̛̛̬͚̮̜̟̣̤͕̼̫̪̗̙͚͉̦̭̣͓̩̫̞͚̤͇̗̲̪͕̝͍͍̫̞̬̣̯̤̮͉̹̫̬͕̫̥̱̹̲͔͔̪̖̱͔̹͈͔̳͖̩͕͚͓̤̤̪̤̩̰̬͙̞͙̘̯̮̫͕͚̙̜̼̩̰̻̞̺͈̝̝̖͎̻̹̞̥̰̮̥̙̠͔͎̤̲͎͍̟̥̞̗̰͓͍̞̹͍̬͎̲̬̞͈͉̼̥̝͈̼̠̫̙͖̪̼̲̯̲̫̼̺̘̗̘͚̤͓̯̦̣̬͒̑̒́͑͊̍̿̉̇̓̒̅̎͌̈́̐̽͋̏̒͂̈̒̃̿̓̇̈̿̊̎̈́͐̒͂͊̿̈́̿̅̏̀͐͛̎̍͑͂̈́̃̇̀̈͋̾̔̈́̽͌̿̍̇̅̏̋̑̈́̾̊͐̉̊̅͑̀͊̽̂̈́̽̓͗́̄͆̄͑͒̈́́͋̏͊͋̒͗̆̋̌̈̀͑͗̽͂̄̌̕͘͘̚͘̕̕͜͜͜͜͜͜͜͠͝͝͝͝͝͝ͅͅͅ ̷̧̡̧̨̢̧̨̡̨̧̛̛̛̛̮̭͇̣͓̙̺͍̟̜̞̫̪̘̼̞̜̠͇̗̮͕̬̥͓͔͈̟̦͇̥̖̭̝̱̗̠̘̝̹̖͓̝͇̖̫̯̩̞̞̯̲̤̱̻̤͇̲͍͈͓͖̹̗̟̲̪̪̟̩͙̪̝̮̘̽̋̍́̔̊̍̈́͂̌̽͒̆͐͊̏̐͑͛̓̆̈́͌̂͒͆̔̅̓̽͊̅́̾̽̓̏̆̀̀͌̾̀͒̓̇̊̀̐͛̌̋̈͑̇́̂̆̽̈̕̕̚̚͜͠ͅͅͅͅḑ̶̛̛̯͓̠̖͎̭̞̫͑̋̄̄̈̽̎̊͛̽͌̾̋̔̽̔̀̀͐̿̈́̀̃͐͂͆̈̃͑̀̋̑͊̃̆̓̾̎̅̀̆̓̏͊̆̔̈̅͛̍̎̓̀͛͒́̐͆̂̋̋͛̆̈͐͂̏̊̏̏̓̿̔͆̓̽̂̅͆̔͑̔̈̾̈̽̂̃̋̈́̾̎̈́̂̓̃̒͐͆̌̍̀͗̈́̑̌̚̕̕̚͠͠͝ę̴̧̨̨̨̢̨̢̧̧̧̨̧̛̛̛̛̛̛̛̺̪̹̘͈̣͔̜͓̥̥̟͇̱͚͖̠͙͙̱̞̣̤͚̣̟̫̬̟͓̺͙̬͚̹͓̗̬̼͇͙̻͍̖̙̥̩͔̜͕̖͕͔͚̳͙̩͇͙̺͔̲̱̙͉̝̠̤̝̭̮̩̦͇̖̳̞̞̖͎̙͙̲̮̠̣͍̪͙̰̣͉̘͉̦̖̳̫͖͖̘̖̮̲̱̪͕̳̫̫̞̪̜̞̬͙͖͍͖̦͉̯̟̖͇̩͚͙͔̳̫͗̈́̒̎͂̇̀͒̈́̃͐̉͛̾̑̆̃͐̈́̉͒̇̓̏̀͌̐͌̅̓͐́̿͒̅͑̍̓̈́̉̊́̉̀̔̊̍̽͛͛͆̓̈͋̉͋̿̉́̋̈̓̐̈́̔̃͆͗͛̏́̀̑͋̀̽̔̓̎̒̆̌̐̈́̓͂̐̋͊̌͑̓̈́̊̿͋̈́́̃̏̓̉͛͆̂͐͗͗̾̅̌̾͌̈́͊͘̕̚̕̚̚̕͘̕͜͜͜͜͜͜͜͠͝͝͠͝͝͠ͅͅa̸̡͔̯͎̟͙̖̗͔̺̰͇͚̭̲̭͕̫̜͉̯͕̅̈͋̒͋͂̐̕ͅţ̶̡̨̢̢̡̡̡̨̢̡̧̨̢̛̥̭̞͈̼̖͙͇̝̳͇̞̬͎̲̙̰̙̱̳̟̣̗̫̣͉͖̪̩͙̲͇͙̫̘͖̖̜̝̦̥̟̜̠͔̠͎̭͔̘͓͚̩͇͙͎͎̰̘̟̳̪͖̠̪̦̦̫̞̟̗̹̹̤͓͍̜̯͔̼̱̮̹͎͖͍̲͎̠͉̟͈̠̦̯̲̼̥̱̬̜͙̘͕̣̳͇̞͓̝͈̼̞̻͚̘̩̟̩̖̼͍̯̘͉͔̤̘̥̦͑̒͗̅̉̾͗̾̓̈́̍̉̈́͛̀͊̋̀͐̏̈́̀̀̍̇̀̀̈́̃̀̅͛̅̈́̇̽̆̌̈̄͆̄̂͂̔͗͌͊̽̿́͑̒̾̑̊̿͗́̇̋̊̄̀̍̓̆͂̆̔̏̍̑̔̊̾̎̆͛͑̓͒̈̎͌̓͗̀̿̓̃̔̈́͗̃̓̽̓̉̀͛͂̿́̀̌͊̆̋̀̓̇́̔̓͆̋̊̀̋͑́̔́̌̒̾̂̎̋̈́́̀͗̈́̈́́̾̈́͑͋̇͒̀͋͆͗̾͐̆̈́͂͐̈̐̓̍̈́̈̅̓͐̚̚̚̚̕͘̕͘̚̚̚͘͜͜͜͜͜͜͝͠͠͠͝͠ͅͅḥ̴̨̧̧̢̧̢̢̛̛̙̱͚̺̬̖̮̪͈̟͉̦̪̘̰̺̳̱̲͔̲̮̦̦̪̪̲̠͓͎͇͕̯̥͉͍̱̥͓̲̤̫̳̠̝͖̺̙͖͎͙̠͓̺̗̝̩͍͕͎̞͕̤̻̰̘͇͕̟̹̳͇͈͇̳̳̞̗̣͖̙͓̼̬̯͚͎̮͚̳̰͙̙̟̊͆͒͆͌̂̈́̀́̽̿͌̓́̐̑͌͋͆͊͑͛͑̀̋͐̏͌̑̀͛͗̀́̈̀̓̽̇̐̋͊̅͑̊͒̈́̀̀̔̀̇͗̆͑̅̌̑̈́͌̒̅̌̓͋͂̀̍̈́͐̈́̆̐̈́̍͛͂̔̐̎͂̎̇͑̈́̈́̎̉̈́́̒̒̆̌̃̓̈́͂̽̓̆̋̈̂̽̆̓̔͗̓̀̄̈́̂̏͗̐̔͘̕͘͘͜͜͜͜͠͠͝͠͠͝͝͝͠͠͝ͅͅ", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 6:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Slave Pass** 🤖\nCongratulations!!!\nCall your boss and take a day off now!", footer="Full Auto and Botting are forbidden", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 16:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Chen Pass** 😈\nCongratulations!!!\nYour daily honor or meat count must be composed only of the digit 6.", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 21:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Carry Pass** 😈\nDon't stop grinding, continue until your Crew gets the max rewards!", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 26:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Relief Ace Pass** 😈\nPrepare to relieve carries of their 'stress' after the day!!!", footer="wuv wuv", thumbnail=ctx.author.avatar_url ,color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Free Leech Pass** 👍\nCongratulations!!!", thumbnail=ctx.author.avatar_url ,color=self.color))
            return
        elif c == 3:
            h = h * random.randint(50, 80)
            m = m * random.randint(50, 80)
        elif c <= 6:
            h = h * random.randint(20, 30)
            m = m * random.randint(20, 30)
        elif c <= 9:
            h = h * random.randint(8, 15)
            m = m * random.randint(8, 15)
        elif c == 10:
            h = h // random.randint(30, 50)
            m = m // random.randint(30, 50)
        elif c <= 12:
            h = h // random.randint(10, 20)
            m = m // random.randint(10, 20)
        elif c <= 14:
            h = h // random.randint(3, 6)
            m = m // random.randint(3, 6)
        h = h * 100000
        m = m * 10

        if ctx.author.id == self.bot.ids.get('chen', -1):
            c = random.randint(3, 8)
            if c == 3: h = 666
            elif c == 4: h = 6666
            elif c == 5: h = 66666
            elif c == 6: h = 666666
            elif c == 7: h = 6666666
            elif c == 8: h = 66666666
            c = random.randint(1, 4)
            if c == 1: m = 6
            elif c == 2: m = 66
            elif c == 3: m = 666
            elif c == 4: m = 6666

        await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="**Honor:** {:,}\n**Meat:** {:,}".format(h, m), thumbnail=ctx.author.avatar_url ,color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 7, commands.BucketType.user)
    async def character(self, ctx):
        """Generate a random GBF character"""
        seed = (ctx.author.id + int(datetime.utcnow().timestamp()) // 86400) % 4428
        rarity = ['SSR', 'SR', 'R']
        race = ['Human', 'Erun', 'Draph', 'Harvin', 'Primal', 'Other']
        element = ['fire', 'water', 'earth', 'wind', 'light', 'dark']

        final_msg = await ctx.send(embed=self.bot.buildEmbed(author={'name':"{}'s daily character".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="**Rarity** ▫️ {}\n**Race** ▫️ {}\n**Element** ▫️ {}\n**Rating** ▫️ {:.1f}".format(self.bot.getEmote(rarity[seed % 3]), race[(seed - 1) % 6], self.bot.getEmote(element[(seed - 3) % 6]), ((seed % 41) * 0.1) + 6.0 - (seed % 3) * 1.5), inline=True, color=self.color))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(30)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def xil(self, ctx):
        """Generate a random element for Xil"""
        g = random.Random()
        elems = ['fire', 'water', 'earth', 'wind', 'light', 'dark']
        g.seed(int((int(datetime.utcnow().timestamp()) // 86400) * (1.0 + 1.0/4.2)))
        e = g.choice(elems)

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Today, Xil's main element is", description="{} **{}**".format(self.bot.getEmote(e), e.capitalize()), color=self.color))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(30)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 30, commands.BucketType.guild)
    async def dragon(self, ctx):
        """Generate two random dragon for today reset in GBF"""
        possible = [
            "{} Wilnas".format(self.bot.getEmote('fire')),
            "{} Wamdus".format(self.bot.getEmote('water')),
            "{} Galleon".format(self.bot.getEmote('earth')),
            "{} Ewiyar".format(self.bot.getEmote('wind')),
            "{} Lu Woh".format(self.bot.getEmote('light')),
            "{} Fediel".format(self.bot.getEmote('dark'))
        ]

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{}'s daily dragons are".format(ctx.author.display_name), description="{} {}\n{} {}".format(self.bot.getEmote('1'), random.choice(possible), self.bot.getEmote('2'), random.choice(possible)), thumbnail=ctx.author.avatar_url, color=self.color))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(30)
            await final_msg.delete()
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, hidden=True, aliases=['leaks', 'leek'])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def leak(self, ctx):
        if random.randint(1, 1000) == 1:
            r = 365
            bingo = True
        else:
            r = random.randint(1, 5)
            bingo = False
        if not isinstance(self.bot.extra, dict): self.bot.extra = {}
        self.bot.extra['leak'] = self.bot.extra.get('leak', 0) + r
        self.bot.savePending = True
        title = "Alliah has been delayed by {} day".format(r)
        if r != 1: title += "s"
        if bingo: title = ":confetti_ball: :partying_face: " + title + " :partying_face: :confetti_ball:"
        msg = await ctx.send(embed=self.bot.buildEmbed(title=title, footer="{} days total".format(self.bot.extra['leak']), color=self.color))
        if not bingo:
            await asyncio.sleep(30)
            await msg.delete()