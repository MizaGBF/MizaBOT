import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import math
from operator import itemgetter

class GBF_Game(commands.Cog):
    """GBF related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xfce746

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    def isGBFGgeneralAndMod(): # for decorators
        async def predicate(ctx):
            return (ctx.channel.id == ctx.bot.ids['gbfg_general'] and ctx.author.guild_permissions.manage_messages)
        return commands.check(predicate)

    # used by the gacha games
    def getRoll(self, ssr, sr_mode = False):
        d = random.randint(1, 10000)
        if d < ssr: return 0
        elif (not sr_mode and d < 1500 + ssr) or sr_mode: return 1
        return 2

    legfestWord = {"double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"}
    def isLegfest(self, word):
        if word.lower() in self.legfestWord: return 2 # 2 because the rates are doubled
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

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['1'])
    @isAuthorized()
    @commands.cooldown(60, 60, commands.BucketType.guild)
    async def single(self, ctx, double : str = ""):
        """Do a single roll
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        r = self.getRoll(300*l)

        if r == 0: msg = "Luckshitter! It's a {}".format(self.bot.getEmote('SSR'))
        elif r == 1: msg = "It's a {}".format(self.bot.getEmote('SR'))
        else: msg = "It's a {}, too bad!".format(self.bot.getEmote('R'))

        await ctx.send(embed=self.bot.buildEmbed(title="{} did a single roll".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['10'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def ten(self, ctx, double : str = ""):
        """Do ten gacha rolls
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
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

        await ctx.send(embed=self.bot.buildEmbed(title="{} did ten rolls".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['300'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def spark(self, ctx, double : str = ""):
        """Do thirty times ten gacha rolls
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        result = self.tenDraws(300*l, 30)
        msg = "{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/300)

        await ctx.send(embed=self.bot.buildEmbed(title="{} sparked".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['frenzy'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def gachapin(self, ctx, double : str = ""):
        """Do ten rolls until you get a ssr
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        result = self.tenDraws(300*l, 0, 1)
        count = result[0]+result[1]+result[2]
        msg = "Gachapin stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Gachapin".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mook'])
    @isAuthorized()
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

        await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Mukku".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorized()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def roulette(self, ctx, double : str = ""):
        """Imitate the GBF roulette
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        mode = 0
        roll = 0
        rps = ['rock', 'paper', 'scissor']
        d = random.randint(1, 36000)
        ct = self.bot.getJST()
        fix200S = ct.replace(year=2020, month=1, day=3, hour=18, minute=0, second=0, microsecond=0)
        fix200E = fix200S.replace(day=5)
        if ct >= fix200S and ct < fix200E:
            msg = "{} {} :confetti_ball: :tada: Guaranteed **2 0 0 R O L L S** :tada: :confetti_ball: {} {}".format(self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'))
            roll = 20
            d = 0
            if l == 2: footer = "3% SSR rate ▪️ You won't get legfest rates, you fool"
            else: footer = "3% SSR rate"
            l = 1
            mode = 3
        elif d < 300:
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
        if d >= 2000 and random.randint(0, 2) > 0:
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

        await ctx.send(embed=self.bot.buildEmbed(author={'name':"{} spun the Roulette".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        #await ctx.send(embed=self.bot.buildEmbed(title="{} spun the Roulette".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setcrystal', 'setspark'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def setRoll(self, ctx, crystal : int, single : int = 0, ten : int = 0):
        """Set your roll count"""
        id = str(ctx.message.author.id)
        try:
            if crystal < 0 or single < 0 or ten < 0:
                raise Exception('Negative numbers')
            if crystal > 500000 or single > 1000 or ten > 100:
                raise Exception('Big numbers')
            if crystal + single + ten == 0: 
                if id in self.bot.spark[0]:
                    self.bot.spark[0].pop(id)
            else:
                self.bot.spark[0][id] = [crystal, single, ten]
            self.bot.savePending = True
            try:
                await self.bot.callCommand(ctx, 'seeRoll', 'GBF_Game')
            except Exception as e:
                await ctx.send(embed=self.bot.buildEmbed(title="Summary", description="**{}** crystal(s)\n**{}** single roll ticket(s)\n**{}** ten roll ticket(s)".format(crystal, single, ten), color=self.color))
                await self.bot.sendError('setRoll', str(e), 'B')
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Give me your number of crystals, single tickets and ten roll tickets, please", color=self.color, footer="setRoll <crystal> [single] [ten]"))
            await self.bot.sendError('setRoll', str(e), 'A')

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['seecrystal', 'seespark'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def seeRoll(self, ctx, member : discord.Member = None):
        """Post your roll count"""
        if member is None: member = ctx.author
        id = str(member.id)
        try:
            # get the roll count
            if id in self.bot.spark[0]:
                s = self.bot.spark[0][id]
                if s[0] < 0 or s[1] < 0 or s[2] < 0:
                    raise Exception('Negative numbers')
                r = (s[0] / 300) + s[1] + s[2] * 10
                fr = math.floor(r)
            else:
                r = 0
                fr = 0

            # calculate estimation
            # note: those numbers are from my own experimentation
            month_min = [90, 80, 145, 95, 80, 85, 85, 120, 60, 70, 70, 145]
            month_max = [65, 50, 110, 70, 55, 65, 65, 80, 50, 55, 55, 110]
            month_day = [31.0, 28.25, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]

            # get current day
            now = self.bot.getJST().replace(hour=0, minute=0, second=0) + timedelta(days=1)
            t_min = now
            t_max = now
            r_min = r % 300
            r_max = r_min
            while r_min < 300 or r_max < 300: # increase the date until we reach the 300 target for both estimation
                if r_min < 300:
                    m = (t_min.month-1) % 12
                    r_min += month_min[m] / month_day[m]
                    t_min += timedelta(days=1)
                if r_max < 300:
                    m = (t_max.month-1) % 12
                    r_max += month_max[m] / month_day[m]
                    t_max += timedelta(days=1)

            # roll count text
            title = "{} {} has {} roll".format(self.bot.getEmote('crystal'), member.display_name, fr)
            if fr != 1: title += "s"
            # flavor text
            if r >= 1200: description = "0̴̧̛͙̠͕͎̭͎̞͚̥̹̟̫̳̫̥͍͙̳̠͈̮̈̂͗̈́̾͐̉1̶̧̛̼͉̟̻̼͍̥̱͖̲̜̬̝̟̦̻̤͓̼̰̱͔̙͔̩̮̝̩̰̐̾͐͑̍̈́̈̋̒̊̔̿́͘͝ͅ0̶̨̢̢̢̨̧̨̡̧̛̛̱̲̫͕̘͍̟̞̬͍͇̜͓̹̹̗̤̗̖̻̞͈̩̪̗̬̖͍̙͙̗̩̳̩̫͕̥̘̩̲̲̩̈́̏̀̽͑̅̔̇̎͂͗̄̂̒̈̇̊̎̔͐̍̓̓̆͒͑̾̓̿̊̀̎̈́̓̂̉̎̉̋̆̇̆̍̈́͗͂̚͘͘͘̚̚̚͜͜͜͝͝͝ͅ1̷̢̧̫͖̤͉̞͓͖̱͎͔̮͔̺̺͈̜͔͇̦͍͓̲̩̼̺̹͙̪̺͉̰͚̺̗̹̝̥̱͍̥͚͓̲̻̣͈̣̥̆̑̋͒̆̆̒̐͑́̏̀̋̍̅͂̇͛̑́̏͑̑͛̈́̒͜͜͠͝͠͝ͅ0̸̧̧̻̦̱̳͖̝̣̻̩͒͂̓̒̈́̆̓̑̅̎͗̓͛͗̍̃̈́̒̈̄̄̚͠͝0̷̢̨̛͔͍̝͉̗͇̫͈̣̳̼͙͓̮̞̻̫̝͓̬̼̲̘̼̫̤͎͛̈̒͒̎͊̌̑̂̉̂̍͂̀̐̈́̓̓̃͊̈́̑̍͂̋̐͂̕͜͝͝1̵̢̡̡̧̡̨̘̖͓̭̩͍̦̭͍̭̙̜̝̙̹̰̻͖̳̱̫̦̙͓̙̺̮͈̳͇͍̹̗̬̖͇͉̳̃̏͗̉ͅ1̴̡̢̨̨̯̺͕̮͈͈̪̮̘̱͓̜̗͓͓͚͕̱̮̬͈̦̖͚̪̬̠͎̫̻̯̭̫̫̜̺̪̞̝̞͖͈͓̖͓̼̲̓̓̈̿̒̋̏̓͂̋̔̿̀̌̏̐̓͑̎̓͐̃̇͑͐̒̀̑͗̇̀̃͘͘̚͜͝ͅ0̷̨̡̡̧̨̛̣͕̖͎̱͚̦̯̻̳̠̞͇̙̣̜͎͍̬̹͖̟̖̠̘̪̞͓͖̫̣̹̫͓̯̖̯͓̻̯̘̫̣̤̤̝̘͙̣͇̯̥̓̒͐͂̄̈́̾͋͐̃̍͛̍͒̓̌̌̇̋͌͂̎̽̇́̈́̒̈́̑̿̈́̇͊̀̽̿͛́͆̊͒͒͊̀̄͌̈͑͂̄̏̿̕̚̕͘͜͠͝͠ͅ1̷̛͕͎̲̙̦͑̔̐̀̊́̊̾̊͂͊̎̀̂͊͐̍́̀̓̊͊̒͊̇̋̉̂̏͌̀̈̓̚͝ͅ1̵̡̡̡̨̧̢̳͉̺̯͓̗̞̺̯͔̯̫̠̮̭͉̗̬̝̜͙̥̠̝͈̯͍̜͉̪̺̘̈̌̏̆̄1̴̛̺̋̄͛̈́́̒̈́̊͂͊͆̍̇̔͊̐̎̇̆̃̈́̈́̌̉̈́̽͑́͑̆̋̀̽̍̎͛̿̊͊̊͛̄̄̓̌́̓́̿̓́̓͘̚̕͠͝͝͠0̸̛͓̑̍̊̒0̵̢̧̪͉̖͕͇̟͔̟͕͙̠͎̥̝̣̬͕͚̤̟͙̣̳̲͆̒͂͆̿̍̈́̕0̴̨̨̧̢̛͚̦̟̟̩̳̘̮͔̭̰̘̹̱͉͕̱̭̬̦̮͈̜̙̻̼̝͚̳͔͎͔͈̦͉̤͔͕͊̉̽̄̋͒͛͒̓̊̃̔͒͌͑̈́̆̅́̍͋̅̏̈́́͒̆̍̽͌́̕̚̕̚͜ͅ0̷̧̧̡̨̱̺̤̪̝͈̲̪̻̹̞̰̼̣̻̮̠͙͚̤̻͚̘̠͔͓͈͎̙͉̩̰͎͍̤̼̞̜̦̲͍̲̭͈̱̠͕̲̯͍͋̑̐̎̉̆̇̉̚͜͜͝ͅͅͅͅ0̶̡̲̼̦͎̬͚͉͓̻̝͙̪̪̫̭̥̰̺͈̜̝͖̭̰̤̈͂̈͌͊͛͆̔̓̉̍̍̇̃͂̇̔̿̾̒̆̓͊͊̑̍̅̔͆͝͝ͅ1̸̛̛̛̛̼͙͇̗͈͚̤̅͛͊̾͌̌̌̑̒̆̐̇̃̎̅̈́̂͋̽͗̀̐̎̒͊̏̿̓̐͆́̒̐̋̌̂͂̈̀̚͠͝1̷̡̨̧̢̡̨̝̟͚̜̞̻͙̳̻̣̱̗̬̠̘̤̪̮̻̟͔̺̥̳̯͔̲͈͉͇̥̼̘͖͉̼͙̠͓̘̯̱̜̗̼͓͓̳̠͊͌͌͛̌́̉̽̿͐̆͌̽̕͜ͅͅͅ0̴͙̩̤̳̼̼̰̲͍̝̳͎̭̙͓̙̱͉͚̯̌̋̐̒̒̍́́̏̍̈́͐̀͗̓͋̿̋̏0̵̡̧̡̢̨̣̻͖̹͕̬͉̟̰̱̬͙̪̬̰̫͖͚̩̪̘͖͓̫̣͉̮̲͎̘͓̗̥̦̞͇̖̦̩̼̮̝̙̈́͐̇̇̄̿̒̆̓̐̌̄̃̐͐̃͆̄̂̉͑͋̉͆͋̓͊̆͌̆̍̔̍͐̈́̾̓͋͗̀̈́͌̓͋̐̉͂͗̒̕̚͘͠͝͝0̸̧̢̨̡̨̧̛̖͙̰̮̙͉̬̬̪̟̮̣̫̳̭̤̞̖̩͔̰̣͇͓͓͋͂͂̄̉̀̊͂̌̍͋̒̋̋̓͂̽̌́̎̀̄̅̄̒̉͐̓͑͐̃̿̍̕̕͘͠ͅ0̸̡̢̡̧̛̪̫̺̪̩̜̜̼̘̺͚͉̩̮͍̜̪̪̪̰́̓͊̾̽̃̿̅͗̏̐̅͗̅͋̇̓̑͆͌͂̅̃͋͒̿̔͛̀̄̐͂͊̒̂͋̕̚͜͝͝͠1̷̛̛̛̫̙̝̺̹̜͕̮̺͈̏̽͛͒̃̈́͐̂̓̍͒́̑̃̒̒͋̅̐̋̌͗̎͒̓̊̉͒͒͗͋̓̓́̅̊̋̽̚͘͝͝͝͝͠0̸̧̨̢̡̧̡̧̛̼̦͓͔͍̠͇̯̘͓̮̼̠̼̫̝̮̪̹̘̘̗̬̫͍̺̭͈̜̲̭̳̜̹̖̩͋̓͋̈́́̈̍̇́͋̋̔̌̀̓̓͊͐̃̇̎́̋̈̀͛̎̒̏̊͂͗̕͝͝͝͝͠ͅ1̸̛̦̉̇̐̒̈͑̾̽͒̈̋̏̍̅̈̈́̊̂̾̀̕̚͘͘̕͝1̷̛̮̱͇̮̦̞̝̣͔̇́̍̔̄̀͂̏̿͗̎̚̕͘ͅͅ1̸̺̭̼̤̩̫̬̳͇̗̭̬̫̺͍̳̠͆̈́̔̓͋̄̈́̀̒̔̅͋̅̓̑̊͑̿̉͒͌̍̓̆͊́̚͝͝͝͝ͅ0̴̨̨̨̘̞͓̮̬̹̪͉̻͎͔̪̗͙̉̈̆̈͋͒̾̊͐̐͆̈̉̇̈́̏́̌͗̍̏̒̋̔͒͒͘̚̕͘͠͝ͅ0̴̡̧̛̭̘̞̹̮̼̼̥̫̯͚̮̙̮͓͚̝͇̆̓͂̇͂͒̆̒̂̀͆́̇̉̈́̐̀̿̌̎̿̃͛̊̄̑̃͛̍͂͒̚̚͜͜͠1̸̢̧̢̧̨̛̛̱̠̖̫̬̦̘͓͍̯̺̞͈̱̞͔̮̮̪͔͚̟̞̰̠̪͑̅̀̈́̀̈́͑̏̋̈́̂̓̄́͋̿͌̇͑̈̈͛̀̈͐̃̄͛́̊̌̂͋͒̉̀̀̍͆͒͆̈́͌̎̍̃͌͜͝͝͝͠ͅͅ0̸̻̺̱̦̖͈̯̼͙̳̤͉̬̫͖͚̲̝͖͈͉̼̺̲̬̣̘̦̺͈͕̈̅̌͂̋̋̏̀͒́͌̐̀̄͆͐̐̊́́̄́̓́̑̾͗̃͒̋̽̍̆̚̕͘͜͝͝͝ͅ0̶̨̧̨̡̗̣̬͍͈̱̣̭͉͌1̵̨̛̛̛̘͍̠̟̹͚̟͚̻͚͔̗̘̻̭͙͇̇̀͂̉̂͛̎̂́̽̒͗̑̾̊̅́͛͗̾͌̉͌́͌̔͆̊͆̍̊̔͂͑̓̊̓̋̿͌́̇̀̃́͆̐͗̿̋̑̓̚̕͜͝͝1̵̧̧̛̘͕̹̥͔̻͇͖̪̘̙̪̯̭̺͓͎̣̳̦̻̻͓͍͓̹̙̲̝̘̞̱̯̝̘̖͓̤̜̭͙͎̑̃̃̌͆̃͌̋͋̾͒̈́̎͌̈́͒̆̌͆̅̀̅͑̑̿͌̏̀̇͗̈́̚̕͜͠͝͝ͅ0̴̢̧̨̧̡̢̡̡̝̖̥̖̮̲͔͚̳͙̹̪̣̭̹̠̪̯͍͇̼͈̙̭͈̤̤̼̺̱̰̥̭̺͇̘̻͙̺̮̹͚̯̤̩̹̟̝̟́̔̊̀̊̽̓͜͜1̵̡̨̨̛̺͎̤̰̤͎̯̮͔͎͇̱̠̳͙̻̳̗̬͙̼̱͈̰͓͕͕͔͍̫̼̯͖̘͒̓̒͆̎̋̆͌͌̿̾̑̀̑̄͐̈́͑̒͗̔͋̾̿̐͑͂͊͐͆̿͑͐͗̐̑̈́̅́̍̋̎̃͂̌̃͘͘͘͘͘̕͠͠0̶̨̨̧̨̢̪͙̩̜̩̟͍̮̟̪̙͚̭̭͇̲̹̟̳͙͇̥̗̭̹̺̥͇̮̞͙̹͎̍̃̎̊̐̎͜͜͜1̸̡̨̡̢̢̧̨̠̝͉̤̹̺̠͕̹̬̝̳̟̦͙͕̯̦̟̰͚̹͙͔̫͖̹̪̙̪̞̖̠͔́͗̓͜ͅͅ1̸̢̨̛̛͍̣̠̠̭̯͈̱͕̘̼͖͖͇̠̰̟̙̪̪̳͙̞̭͉͙̓̔̈́͌͑̌͑̉̈́́͌̍̿̀͌͂̎͊̎̇̌̆̒͊͒͆͊̆́͐̕͘̕͝͠͠ :robot:\n"
            elif r >= 1150: description = "P̶̧̢̺̜̮̟̼͔͔̻̲̩͎̘̖̲̐͂̑͂͛́͑̍̊̓͌̀̃͛͊͑͋̑̽̀́̆̀̔͋̋̂̏͒̀̎̈̾͑̉̅͒̉͂̑͒̕̕̚̚͝͝͝͝͝͝͝ļ̴̡̩͓͙̪̫̥͇͈͈̪̭̣̲͇̥̪͍̫̼̟͙̱̟̤̩̬͇̬̝͇̞͆͆͆̓̾̎͌̈͆̾̅̀͐̄̇̈́̔̊́̾̈͗̊̏̊̀̀̕̚̕͜͝͝ͅe̵̡̢̨̢̨̧̨̛̛̗̪̟̼̘̤̻̭̮̙̼̞͙̲̗̟͔̠̲̦̯̖̪̪͖̱̳̼̺͎͎̬̜̤̣͍̩̫̱̪̮̰̗̲̫̾̀̀̍̈́͂͋̑͑̑͒̈́̊͊̑́̐̅̿̈́̎͗̀̔̍̔̋̍̄͊̑̆̀̏̏̈́̀̉̈̐̅̚͘͘͜͜͝͝ͅͅȧ̴̢̢̧̧̢̡̳͕̲͖̰͔̝͖̱̙͙̫̞͕̮̫̼̤̹͔̫̹͉͚̞̠̬͎̘̯̱̳̯̠̪̰͎̖̻̹̖̜̪̣͍͋̄̐̍̽̒̓̀̐̈́̚͜ͅͅs̷̢̨̡̡̢̛̛̙̫̮͙̤͎̗̭̯̭͚̖͕̰̜̱̘̥̝͖̺͇̳̥̆͒̽͒̓̅̀́̽͌͌͌͂̉͛̊͌̌̉̌̋̈̀̽̍̀̔̋̀̒͒̃̌̊̆̍̀͊̐̐̇̑̽̊͘̕̕͝ͅe̶̢̧̨̢̧̨̝̗̝̠͙̳̼̙̤͍̠͖̙̖̱̳̼̘͉͍̲̦͉̝̞̞̬̮̝̱̥̪̟̯̹̹̘͇̗̯͓̬͖͐̓͛͛̓̌̂͊̚͘͠ͅ ̴̧̢̩̪̥̺̼͙̺̱̞̩̞͕͇̰͔̙͎͈̼̠̮͓̬̺͍̥͍͙̰̮̹̔̈͒̋͂͋̇̿̀̓̏̋̋̅̓͘̚͜͠͝͝Ş̵̛̛͇̙̟̼̤̫̱͖͖̮̩̹̭̮̣̩̫̙̳̗̜͓̪̻̖͇̼͖̣̝̈̏̏̈́̍̍̃̓̒̾̎͐͗͂̑͐͆̃͐̎̽͂͆͊̐̀̎̂͗̀́̿̎̆̀̾́̃̃̌̒̍̓͌̉̍̕͘̕͝͠͝ͅp̵̡̧̙͈̗̟͚̳̱͔̳̺̟̤̞̰̺̫̤͙̜̩͚̹̰͎͚͕̭͕̀̈̈̉̎̔̇ͅͅa̷̢̧̢̧̨̙͔͇͈̭̥̦͖̭̲͎̥͈͚͖̟͓̱͚͉̰̣͍͉̰͇͔̖̲̖͙̫̰̜̯̦͆̌̋̂̀̓͊́̓̄̒̈́̓͌̅́́̀͑́͊̚̕͜ͅŗ̵̡̗̲͇̺̰̭͕̪̩͋̊̎̔͒͛̈́̿͊͂̂̏̑́̉́͒͌̑̎͐͊̒͂́̄̋́͋͂̅̅͗͊̕̚͘̕̕̚͘͠͠ͅķ̵̨̧̧̹̩͇̣͔̤̦͍͉̘̘̹̹̠̪̰͉̗̯̦̣̘͉̳̦̼̥͕̣̪̭̩̦̥͓̝̣̰͉̻̇̈́̾̈͊̈́͗̈́̈́̌̂̈́͒̏̐͆̀̔̿̉̅̈́̀̈́͌̌̈͊̐̂͒̓́̀͛̌͘̚͘͘̚͘͜͜͝͝͠͠ :robot:\n"
            elif r >= 1100: description = "Į̵̨̡̧̧̢̧̧͈͍͓͎̻͓͚̼̭̬̺̠̺̘̰̬̖̥̘̪̞̠̟̦̪͕̺̙͍͈̭͚̫̤͕̪̖̩̲̜̈́̅̍͛̽̑̐͋̀̅͂̑͋̊͂̒̊̀̂͊̈́͆̃͌̂̆̓́̒̓̈̒̍̑̂̓̕͘͘̕̕̕͝͝ͅͅt̷̨͇̥͇̭̹̀̔́̉͗̃͂̀͗̐̐̈́̎̀͘͜ ̸̡̛̗̭̫̟̫̬͇̲̳̺̗̦̭̤̠̗͓̳̥͉̗̖̰͎̩̬͚̙̯͕̟̭̗̮̤̲̭̲͉̠̦̹͎̩̤̺̖͈̘̞͇͒̂͆͆͗̂͗͛̒̏͒́͛̏͂͋̿͊̽̊͊̂̋́̐͌̇̄͛̐̐̌͒̏̔̑́͐͐͘̕͜͜͝͝͝h̸̢̡͔̗͕̻͍͚̦̪͇̺̘̗̞̭͇̰̼̠̟͉̰̤̞̞͔͙̻̯̬̬̬͓̩̻͖̞͈̙̐̊̓͒̒́͊̓̆̀͑́̌̀̊̓̿̎͛̍̅̋̔́̆̓̎̊̊́̀̄̂̾̎̍̏̒͛̆̇̉͐̏̏̂̃̕̚͘̕̚͠͝ͅŭ̷̢̯̱̤͎̦̥̜͈̉̆̏̊̄̈́̾̍̇͗̈́̈́͑̑́͌́̊̂͂̈́̉̓̐̑̃̾̽̊̂̕̕͜͝͝͝r̴̡̢̫̪͎̜͉͕̹̼̞̭̥̖̼̤̻̥͈͇̓̓͊͂͑̐̉̂̍̈́̏̓͜͝ͅţ̵̛̩̮̝̼̲͚̩̼̖̫̖͔̪̘̫͍̗̭̦̪͒͐̆̔͛̋̑̒̄̓̏̃̎̓̈́͛̇͛͋͗̅̏̊́̿̐͐͌͑͐̎̏̀̏͐̔̊̎̆̽̓̀̄̌́͘͜͝͝͝ͅs̸̛͚̣͛̀́́̌͌̏͌̉̐̒͑͋̐̍̚̕͝ :robot:\n"
            elif r >= 1050: description = "S̷̨̧̢̯̝̱̩̥̺̹̜̬̳̜̳̞̪̳̘̼͓̭͖̮̱͈̼̫̰̘̟̻̞͈̩͔̻̯̥̜͔̭̰̾͌̌̊̍͊͛̊̉̀͛̑̍͆̂̐̔̈̍̅̎̐͊̐̓͂̀͒̾̑̄͗͛̄͊̑̿̿̉́̉̌͋̂̕͜͜͝͠ͅͅţ̸̢̨̢̨̨̳̳̮͉̰͖͈͓͈̖̗̻̭̺̳̮̜͕͕͚̜͎̳͇̹̪̪̯͓̤͔͖͇̣̼̬̺͙̞͉͋͊͐͆̽͜͜ơ̵̡̨̧̰̫͔͓̘̗̺͚̺͓̠̹̤̻̟͖̮͎͎̰̦̤̥̘̹̼̗̭͓̻͈͔̱̈́̔͒͗̈͒̈́͛̎̋͛̌̏͂͂̊͊͊̓̏̈́̑̆͗͊̄̎͒̌̎̈́̀̆͑̒̾͌͂́͌̽̋̕̚̚̕͠͝͝͝͝ṕ̶̨͈̜̰̓̾̏̍̐̊̾̃͑̏̂̐̽̔͋̽̀̈́̍̾͊̑̃̽́̈́̚͜͠͠͝ ̴̛͍͙̺̳͚̖͉̝̜̦̘̥̭̤̹̂̈́̌̀̂͌̑̔͊̅̾͗̊̈͝ņ̵̧̢̳̣̥̙̭̭̖̖̲͓̦̗̩̝͉̦̣͉̬̗̙̘̪̲͖̜̟̫͓̖̦̣̩̝͙̫͈́̋̽͂̓͐͌̀̂̌̑̏͌̍̑̿̒̌͗̽͆͐̈́̆̅̋̆̽̍̅̅̃̑̈́̍̃͘͜͜͝ͅö̵͈́w̷̧̧̧̢̛̛̗̺̪͍̬̪͚͇͇̯͈͓̰̯̻̭̹̺̞̣͍͇̯̪̮̬̙͓̤̱̘̱͓̫̅̈̓͛͗̋̐̓̑̎́̓͆͒͂́̈́̈́͗́̌̌͂͊̄̊̈́̋͌́̓̌̒̑̆̐́̐͛̆̈́̓̓̚̚͝͠͝͝͝͠͝ͅͅͅ :robot: \n"
            elif r >= 1000: description = "ReAcHiNg CrItIcAl :robot:\n"
            elif r >= 900: description = "Will you spark soon? :skull:\n"
            elif r >= 600: description = "**STOP HOARDING** :confounded:\n"
            elif r >= 350: description = "What are you waiting for? :thinking:\n"
            elif r >= 300: description = "Dickpick or e-sport pick? :smirk:\n"
            elif r >= 250: description = "Almost! :blush: \n"
            elif r >= 220: description = "One more month :thumbsup: \n"
            elif r >= 180: description = "You are getting close :ok_hand: \n"
            elif r >= 150: description = "Half-way done :relieved:\n"
            elif r >= 100: description = "Stay strong :wink:\n"
            elif r >= 50: description = "You better save these rolls :spy: \n"
            elif r >= 20: description = "Start saving **NOW** :rage:\n"
            else: description = "Pathetic :nauseated_face: \n"
            # estimation text
            footer = "Next spark between {}/{}/{} and {}/{}/{}".format(t_min.year, t_min.month, t_min.day, t_max.year, t_max.month, t_max.day)
            # sending
            await ctx.send(embed=self.bot.buildEmbed(title=title, description=description, footer=footer, color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I warned my owner", color=self.color, footer=str(e)))
            await self.bot.sendError('seeRoll', str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["sparkranking", "hoarders"])
    @isAuthorized()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def rollRanking(self, ctx):
        """Show the ranking of everyone saving for a spark in the server
        You must use $setRoll to set/update your roll count"""
        try:
            ranking = {}
            guild = ctx.message.author.guild
            for m in guild.members:
                id = str(m.id)
                if id in self.bot.spark[0]:
                    if id in self.bot.spark[1]:
                        continue
                    s = self.bot.spark[0][id]
                    if s[0] < 0 or s[1] < 0 or s[2] < 0:
                        continue
                    r = (s[0] / 300) + s[1] + s[2] * 10
                    if r > 1000:
                        continue
                    ranking[id] = r
            if len(ranking) == 0:
                await ctx.send(embed=self.bot.buildEmbed(title="The ranking of this server is empty"))
                return
            ar = -1
            i = 0
            emotes = {0:self.bot.getEmote('SSR'), 1:self.bot.getEmote('SR'), 2:self.bot.getEmote('R')}
            msg = ""
            top = 15
            for key, value in sorted(ranking.items(), key = itemgetter(1), reverse = True):
                if i < top:
                    fr = math.floor(value)
                    msg += "**#{:<2}{} {}** with {} roll".format(i+1, emotes.pop(i, "▫️"), guild.get_member(int(key)).display_name, fr)
                    if fr != 1: msg += "s"
                    msg += "\n"
                if key == str(ctx.message.author.id):
                    ar = i
                    if i >= top: break
                i += 1
                if i >= 100:
                    break
            if ar >= top: footer = "You are ranked #{}".format(ar+1)
            elif ar == -1: footer = "You aren't ranked ▫️ You need at least one roll to be ranked"
            else: footer = ""
            await ctx.send(embed=self.bot.buildEmbed(title="{} Spark ranking of {}".format(self.bot.getEmote('crown'), guild.name), color=self.color, description=msg, footer=footer, thumbnail=guild.icon_url))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Sorry, something went wrong :bow:", footer=str(e)))
            await self.bot.sendError("rollRanking", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def quota(self, ctx):
        """Give you your GW quota for the day"""
        if ctx.author.id in self.bot.ids.get('branded', []):
            await ctx.send(embed=self.bot.buildEmbed(title="{} {} is a bad boy".format(self.bot.getEmote('gw'), ctx.author.display_name), description="Your account is **restricted.**", thumbnail=ctx.author.avatar_url, color=self.color))
            return

        h = random.randint(300, 2000)
        m = random.randint(50, 150)
        c = random.randint(1, 100)

        if ctx.author.id == self.bot.ids['wawi']:
            c = 7

        if c <= 2:
            c = random.randint(1, 100)
            if c <= 5:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Slave Pass** 🤖\nCongratulations!!!\nCall your boss and take a day off now!", footer="Full Auto and Botting are forbidden", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 15:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Chen Pass** 😈\nCongratulations!!!\nYour daily honor and meat count must be composed only of the digit 6.", thumbnail=ctx.author.avatar_url ,color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Free Leech Pass** 👍\nCongratulations!!!", thumbnail=ctx.author.avatar_url ,color=self.color))
            return
        elif c == 3:
            h = h * random.randint(30, 50)
            m = m * random.randint(30, 50)
        elif c <= 5:
            h = h * random.randint(10, 20)
            m = m * random.randint(10, 20)
        elif c <= 7:
            h = h * random.randint(3, 6)
            m = m * random.randint(3, 6)
        elif c == 8:
            h = h // random.randint(30, 50)
            m = m // random.randint(30, 50)
        elif c <= 10:
            h = h // random.randint(10, 20)
            m = m // random.randint(10, 20)
        elif c <= 12:
            h = h // random.randint(3, 6)
            m = m // random.randint(3, 6)
        h = h * 100000
        m = m * 10

        if ctx.author.id == self.bot.ids['chen']:
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
    @isGBFGgeneralAndMod()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def pitroulette(self, ctx, max : int = 1):
        """Game for /gbfg/ (Mod only)"""
        if not self.bot.pitroulette:
            if max < 1 or max > 5:
                await ctx.send(embed=self.bot.buildEmbed(title="Value must be in the 1-5 range" ,color=self.color))
                return
            self.bot.pitroulette = True
            self.bot.pitroulettecount = 0
            self.bot.pitroulettemax = max
            self.bot.pitroulettevictim = []
            self.bot.pitroulettelist = []
            await ctx.send(embed=self.bot.buildEmbed(title="Pit Roulette enabled", description=random.choice(["Who will fall in?", "Are you brave enough?", "Do you dare?"]) , thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/584813271643586560/Activate_it.png", footer="expecting " + str(max) + " victim(s)", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Pit Roulette already on" ,color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorized()
    @commands.cooldown(2, 7, commands.BucketType.user)
    async def character(self, ctx):
        """Generate a random GBF character"""
        seed = (ctx.author.id + int(datetime.utcnow().timestamp()) // 86400) % 4428
        rarity = ['SSR', 'SR', 'R']
        race = ['Human', 'Erun', 'Draph', 'Harvin', 'Primal', 'Other']
        element = ['fire', 'water', 'earth', 'wind', 'light', 'dark']

        await ctx.send(embed=self.bot.buildEmbed(author={'name':"{}'s daily character".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="**Rarity** ▫️ {}\n**Race** ▫️ {}\n**Element** ▫️ {}\n**Rating** ▫️ {:.1f}".format(self.bot.getEmote(rarity[seed % 3]), race[(seed - 1) % 6], self.bot.getEmote(element[(seed - 3) % 6]), ((seed % 41) * 0.1) + 6.0 - (seed % 3) * 1.5), inline=True, color=self.color))


    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def xil(self, ctx):
        """Generate a random element for Xil"""
        g = random.Random()
        elems = ['fire', 'water', 'earth', 'wind', 'light', 'dark']
        g.seed(int((int(datetime.utcnow().timestamp()) // 86400) * (1.0 + 1.0/4.2)))
        e = g.choice(elems)

        await ctx.send(embed=self.bot.buildEmbed(title="Today, Xil's main element is", description="{} **{}**".format(self.bot.getEmote(e), e.capitalize()), color=self.color))