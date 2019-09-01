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
    def getRoll(self, ssr):
        d = random.randint(1, 10000)
        if d < ssr: return 0
        elif d < 1500 + ssr: return 1
        return 2

    legfestWord = {"double", "x2", "legfest", "flashfest"}
    def isLegfest(self, word):
        if word.lower() in self.legfestWord: return 2 # 2 because the rates are doubled
        return 1

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['1'])
    @isAuthorized()
    @commands.cooldown(60, 60, commands.BucketType.guild)
    async def single(self, ctx, double : str = ""):
        """Do a single roll
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        l = self.isLegfest(double)
        if l == 2: footer = "SSR Rate is doubled"
        else: footer = ""
        r = self.getRoll(300*l)

        if r == 0: msg = "Luckshitter! It's a " + self.bot.getEmoteStr('SSR')
        elif r == 1: msg = "It's a " + self.bot.getEmoteStr('SR')
        else: msg = "It's a " + self.bot.getEmoteStr('R') + ", too bad!"

        await ctx.send(embed=self.bot.buildEmbed(title="{} did a single roll".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['10'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def ten(self, ctx, double : str = ""):
        """Do ten gacha rolls
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        l = self.isLegfest(double)
        if l == 2: footer = "SSR Rate is doubled"
        else: footer = ""
        sr_flag = False
        msg = ""
        i = 0
        while i < 10:
            r = self.getRoll(300*l)
            if r <= 1: sr_flag = True
            if i == 9 and not sr_flag:
                continue
            if i == 5: msg += '\n'
            if r == 0: msg += self.bot.getEmoteStr('SSR')
            elif r == 1: msg += self.bot.getEmoteStr('SR')
            else: msg += self.bot.getEmoteStr('R')
            i += 1

        await ctx.send(embed=self.bot.buildEmbed(title="{} did ten rolls".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['300'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def spark(self, ctx, double : str = ""):
        """Do thirty times ten gacha rolls
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        l = self.isLegfest(double)
        if l == 2: footer = "SSR Rate is doubled"
        else: footer = ""
        result = [0, 0, 0]
        for x in range(0, 30):
            i = 0
            sr_flag = False
            while i < 10:
                r = self.getRoll(300*l)
                if r <= 1: sr_flag = True
                if i == 9 and not sr_flag:
                    continue
                result[r] += 1
                i += 1
        msg = self.bot.getEmoteStr('SSR') + ": " + str(result[0]) + "\n"
        msg += self.bot.getEmoteStr('SR') + ": " + str(result[1]) + "\n"
        msg += self.bot.getEmoteStr('R') + ": " + str(result[2]) + "\n"
        msg += "SSR rate: **{:.2f}%**\n".format(100*result[0]/300)

        await ctx.send(embed=self.bot.buildEmbed(title="{} sparked".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['frenzy'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def gachapin(self, ctx, double : str = ""):
        """Do ten rolls until you get a ssr
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        l = self.isLegfest(double)
        if l == 2: footer = "SSR Rate is doubled"
        else: footer = ""
        result = [0, 0, 0]
        count = 0
        for x in range(0, 30):
            i = 0
            count += 1
            sr_flag = False
            ssr_flag = False
            while i < 10:
                r = self.getRoll(300*l)
                if r <= 1: sr_flag = True
                if i == 9 and not sr_flag:
                    continue
                if r == 0: ssr_flag = True
                result[r] += 1
                i += 1
            if ssr_flag:
                break
        msg = "Gachapin stopped after **" + str(count*10) + "** rolls\n"
        msg += self.bot.getEmoteStr('SSR') + ": " + str(result[0]) + "\n"
        msg += self.bot.getEmoteStr('SR') + ": " + str(result[1]) + "\n"
        msg += self.bot.getEmoteStr('R') + ": " + str(result[2]) + "\n"
        msg += "SSR rate: **{:.2f}%**\n".format(100*result[0]/(count*10))

        await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Gachapin".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mook'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def mukku(self, ctx, super : str = ""):
        """Do ten rolls until you get a ssr, 9% ssr rate
        You can add "super" for a 9% rate and 5 ssr mukku"""
        if super.lower() == "super":
            ssr = 1500
            footer = "Super Mukku ▪ 15% SSR Rate and at least 5 SSRs\n"
            limit = 5
        else:
            ssr = 900
            footer = ""
            limit = 1
        result = [0, 0, 0]
        count = 0
        for x in range(0, 30):
            i = 0
            count += 1
            sr_flag = False
            while i < 10:
                r = self.getRoll(ssr)
                if r <= 1: sr_flag = True
                if i == 9 and not sr_flag:
                    continue
                if r == 0: limit -= 1
                result[r] += 1
                i += 1
            if limit <= 0:
                break
        msg = "Mukku stopped after **" + str(count*10) + "** rolls\n"
        msg += self.bot.getEmoteStr('SSR') + ": " + str(result[0]) + "\n"
        msg += self.bot.getEmoteStr('SR') + ": " + str(result[1]) + "\n"
        msg += self.bot.getEmoteStr('R') + ": " + str(result[2]) + "\n"
        msg += "SSR rate: **{:.2f}%**\n".format(100*result[0]/(count*10))

        await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Mukku".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def roulette(self, ctx):
        """Imitate the GBF roulette"""
        d = random.randint(1, 36000)
        if d < 500: msg = ":confetti_ball: :tada: **100** rolls!! :tada: :confetti_ball:"
        elif d < 2000: msg = "**Gachapin Frenzy** :four_leaf_clover:"
        elif d < 6500: msg = "**30** rolls! :clap:"
        elif d < 19000: msg = "**20** rolls :open_mouth:"
        else: msg = "**10** rolls :pensive:"

        await ctx.send(embed=self.bot.buildEmbed(title="{} spun the Roulette".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url))

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
                await ctx.send(embed=self.bot.buildEmbed(title="Summary", description="**" + str(crystal) + "** crystal(s)\n**" + str(single) + "** single roll ticket(s)\n**" +str(ten) + "** ten roll ticket(s)", color=self.color))
                await self.bot.sendError('setRoll', str(e), 'B')
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Give me your number of crystals, single tickets and ten roll tickets, please", color=self.color, footer="setRoll <crystal> [single] [ten]"))
            await self.bot.sendError('setRoll', str(e), 'A')

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['seecrystal', 'seespark'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def seeRoll(self, ctx):
        """Post your roll count"""
        id = str(ctx.message.author.id)
        try:
            if id in self.bot.spark[0]:
                s = self.bot.spark[0][id]
                if s[0] < 0 or s[1] < 0 or s[2] < 0:
                    raise Exception('Negative numbers')
                r = (s[0] / 300) + s[1] + s[2] * 10
                fr = math.floor(r)
            else:
                r = 0
                fr = 0
            left = (300 - (r % 300))
            spark_time_range = [
                self.bot.getJST() + timedelta(days=(left / 2.8)), 
                self.bot.getJST() + timedelta(days=(left / 2.2))
            ]
            msg1 = self.bot.getEmoteStr('crystal') + " " + ctx.author.display_name + " has " + str(fr) + " roll"
            if fr != 1: msg1 += "s"
            if r >= 1200: msg2 = "0̴̧̛͙̠͕͎̭͎̞͚̥̹̟̫̳̫̥͍͙̳̠͈̮̈̂͗̈́̾͐̉1̶̧̛̼͉̟̻̼͍̥̱͖̲̜̬̝̟̦̻̤͓̼̰̱͔̙͔̩̮̝̩̰̐̾͐͑̍̈́̈̋̒̊̔̿́͘͝ͅ0̶̨̢̢̢̨̧̨̡̧̛̛̱̲̫͕̘͍̟̞̬͍͇̜͓̹̹̗̤̗̖̻̞͈̩̪̗̬̖͍̙͙̗̩̳̩̫͕̥̘̩̲̲̩̈́̏̀̽͑̅̔̇̎͂͗̄̂̒̈̇̊̎̔͐̍̓̓̆͒͑̾̓̿̊̀̎̈́̓̂̉̎̉̋̆̇̆̍̈́͗͂̚͘͘͘̚̚̚͜͜͜͝͝͝ͅ1̷̢̧̫͖̤͉̞͓͖̱͎͔̮͔̺̺͈̜͔͇̦͍͓̲̩̼̺̹͙̪̺͉̰͚̺̗̹̝̥̱͍̥͚͓̲̻̣͈̣̥̆̑̋͒̆̆̒̐͑́̏̀̋̍̅͂̇͛̑́̏͑̑͛̈́̒͜͜͠͝͠͝ͅ0̸̧̧̻̦̱̳͖̝̣̻̩͒͂̓̒̈́̆̓̑̅̎͗̓͛͗̍̃̈́̒̈̄̄̚͠͝0̷̢̨̛͔͍̝͉̗͇̫͈̣̳̼͙͓̮̞̻̫̝͓̬̼̲̘̼̫̤͎͛̈̒͒̎͊̌̑̂̉̂̍͂̀̐̈́̓̓̃͊̈́̑̍͂̋̐͂̕͜͝͝1̵̢̡̡̧̡̨̘̖͓̭̩͍̦̭͍̭̙̜̝̙̹̰̻͖̳̱̫̦̙͓̙̺̮͈̳͇͍̹̗̬̖͇͉̳̃̏͗̉ͅ1̴̡̢̨̨̯̺͕̮͈͈̪̮̘̱͓̜̗͓͓͚͕̱̮̬͈̦̖͚̪̬̠͎̫̻̯̭̫̫̜̺̪̞̝̞͖͈͓̖͓̼̲̓̓̈̿̒̋̏̓͂̋̔̿̀̌̏̐̓͑̎̓͐̃̇͑͐̒̀̑͗̇̀̃͘͘̚͜͝ͅ0̷̨̡̡̧̨̛̣͕̖͎̱͚̦̯̻̳̠̞͇̙̣̜͎͍̬̹͖̟̖̠̘̪̞͓͖̫̣̹̫͓̯̖̯͓̻̯̘̫̣̤̤̝̘͙̣͇̯̥̓̒͐͂̄̈́̾͋͐̃̍͛̍͒̓̌̌̇̋͌͂̎̽̇́̈́̒̈́̑̿̈́̇͊̀̽̿͛́͆̊͒͒͊̀̄͌̈͑͂̄̏̿̕̚̕͘͜͠͝͠ͅ1̷̛͕͎̲̙̦͑̔̐̀̊́̊̾̊͂͊̎̀̂͊͐̍́̀̓̊͊̒͊̇̋̉̂̏͌̀̈̓̚͝ͅ1̵̡̡̡̨̧̢̳͉̺̯͓̗̞̺̯͔̯̫̠̮̭͉̗̬̝̜͙̥̠̝͈̯͍̜͉̪̺̘̈̌̏̆̄1̴̛̺̋̄͛̈́́̒̈́̊͂͊͆̍̇̔͊̐̎̇̆̃̈́̈́̌̉̈́̽͑́͑̆̋̀̽̍̎͛̿̊͊̊͛̄̄̓̌́̓́̿̓́̓͘̚̕͠͝͝͠0̸̛͓̑̍̊̒0̵̢̧̪͉̖͕͇̟͔̟͕͙̠͎̥̝̣̬͕͚̤̟͙̣̳̲͆̒͂͆̿̍̈́̕0̴̨̨̧̢̛͚̦̟̟̩̳̘̮͔̭̰̘̹̱͉͕̱̭̬̦̮͈̜̙̻̼̝͚̳͔͎͔͈̦͉̤͔͕͊̉̽̄̋͒͛͒̓̊̃̔͒͌͑̈́̆̅́̍͋̅̏̈́́͒̆̍̽͌́̕̚̕̚͜ͅ0̷̧̧̡̨̱̺̤̪̝͈̲̪̻̹̞̰̼̣̻̮̠͙͚̤̻͚̘̠͔͓͈͎̙͉̩̰͎͍̤̼̞̜̦̲͍̲̭͈̱̠͕̲̯͍͋̑̐̎̉̆̇̉̚͜͜͝ͅͅͅͅ0̶̡̲̼̦͎̬͚͉͓̻̝͙̪̪̫̭̥̰̺͈̜̝͖̭̰̤̈͂̈͌͊͛͆̔̓̉̍̍̇̃͂̇̔̿̾̒̆̓͊͊̑̍̅̔͆͝͝ͅ1̸̛̛̛̛̼͙͇̗͈͚̤̅͛͊̾͌̌̌̑̒̆̐̇̃̎̅̈́̂͋̽͗̀̐̎̒͊̏̿̓̐͆́̒̐̋̌̂͂̈̀̚͠͝1̷̡̨̧̢̡̨̝̟͚̜̞̻͙̳̻̣̱̗̬̠̘̤̪̮̻̟͔̺̥̳̯͔̲͈͉͇̥̼̘͖͉̼͙̠͓̘̯̱̜̗̼͓͓̳̠͊͌͌͛̌́̉̽̿͐̆͌̽̕͜ͅͅͅ0̴͙̩̤̳̼̼̰̲͍̝̳͎̭̙͓̙̱͉͚̯̌̋̐̒̒̍́́̏̍̈́͐̀͗̓͋̿̋̏0̵̡̧̡̢̨̣̻͖̹͕̬͉̟̰̱̬͙̪̬̰̫͖͚̩̪̘͖͓̫̣͉̮̲͎̘͓̗̥̦̞͇̖̦̩̼̮̝̙̈́͐̇̇̄̿̒̆̓̐̌̄̃̐͐̃͆̄̂̉͑͋̉͆͋̓͊̆͌̆̍̔̍͐̈́̾̓͋͗̀̈́͌̓͋̐̉͂͗̒̕̚͘͠͝͝0̸̧̢̨̡̨̧̛̖͙̰̮̙͉̬̬̪̟̮̣̫̳̭̤̞̖̩͔̰̣͇͓͓͋͂͂̄̉̀̊͂̌̍͋̒̋̋̓͂̽̌́̎̀̄̅̄̒̉͐̓͑͐̃̿̍̕̕͘͠ͅ0̸̡̢̡̧̛̪̫̺̪̩̜̜̼̘̺͚͉̩̮͍̜̪̪̪̰́̓͊̾̽̃̿̅͗̏̐̅͗̅͋̇̓̑͆͌͂̅̃͋͒̿̔͛̀̄̐͂͊̒̂͋̕̚͜͝͝͠1̷̛̛̛̫̙̝̺̹̜͕̮̺͈̏̽͛͒̃̈́͐̂̓̍͒́̑̃̒̒͋̅̐̋̌͗̎͒̓̊̉͒͒͗͋̓̓́̅̊̋̽̚͘͝͝͝͝͠0̸̧̨̢̡̧̡̧̛̼̦͓͔͍̠͇̯̘͓̮̼̠̼̫̝̮̪̹̘̘̗̬̫͍̺̭͈̜̲̭̳̜̹̖̩͋̓͋̈́́̈̍̇́͋̋̔̌̀̓̓͊͐̃̇̎́̋̈̀͛̎̒̏̊͂͗̕͝͝͝͝͠ͅ1̸̛̦̉̇̐̒̈͑̾̽͒̈̋̏̍̅̈̈́̊̂̾̀̕̚͘͘̕͝1̷̛̮̱͇̮̦̞̝̣͔̇́̍̔̄̀͂̏̿͗̎̚̕͘ͅͅ1̸̺̭̼̤̩̫̬̳͇̗̭̬̫̺͍̳̠͆̈́̔̓͋̄̈́̀̒̔̅͋̅̓̑̊͑̿̉͒͌̍̓̆͊́̚͝͝͝͝ͅ0̴̨̨̨̘̞͓̮̬̹̪͉̻͎͔̪̗͙̉̈̆̈͋͒̾̊͐̐͆̈̉̇̈́̏́̌͗̍̏̒̋̔͒͒͘̚̕͘͠͝ͅ0̴̡̧̛̭̘̞̹̮̼̼̥̫̯͚̮̙̮͓͚̝͇̆̓͂̇͂͒̆̒̂̀͆́̇̉̈́̐̀̿̌̎̿̃͛̊̄̑̃͛̍͂͒̚̚͜͜͠1̸̢̧̢̧̨̛̛̱̠̖̫̬̦̘͓͍̯̺̞͈̱̞͔̮̮̪͔͚̟̞̰̠̪͑̅̀̈́̀̈́͑̏̋̈́̂̓̄́͋̿͌̇͑̈̈͛̀̈͐̃̄͛́̊̌̂͋͒̉̀̀̍͆͒͆̈́͌̎̍̃͌͜͝͝͝͠ͅͅ0̸̻̺̱̦̖͈̯̼͙̳̤͉̬̫͖͚̲̝͖͈͉̼̺̲̬̣̘̦̺͈͕̈̅̌͂̋̋̏̀͒́͌̐̀̄͆͐̐̊́́̄́̓́̑̾͗̃͒̋̽̍̆̚̕͘͜͝͝͝ͅ0̶̨̧̨̡̗̣̬͍͈̱̣̭͉͌1̵̨̛̛̛̘͍̠̟̹͚̟͚̻͚͔̗̘̻̭͙͇̇̀͂̉̂͛̎̂́̽̒͗̑̾̊̅́͛͗̾͌̉͌́͌̔͆̊͆̍̊̔͂͑̓̊̓̋̿͌́̇̀̃́͆̐͗̿̋̑̓̚̕͜͝͝1̵̧̧̛̘͕̹̥͔̻͇͖̪̘̙̪̯̭̺͓͎̣̳̦̻̻͓͍͓̹̙̲̝̘̞̱̯̝̘̖͓̤̜̭͙͎̑̃̃̌͆̃͌̋͋̾͒̈́̎͌̈́͒̆̌͆̅̀̅͑̑̿͌̏̀̇͗̈́̚̕͜͠͝͝ͅ0̴̢̧̨̧̡̢̡̡̝̖̥̖̮̲͔͚̳͙̹̪̣̭̹̠̪̯͍͇̼͈̙̭͈̤̤̼̺̱̰̥̭̺͇̘̻͙̺̮̹͚̯̤̩̹̟̝̟́̔̊̀̊̽̓͜͜1̵̡̨̨̛̺͎̤̰̤͎̯̮͔͎͇̱̠̳͙̻̳̗̬͙̼̱͈̰͓͕͕͔͍̫̼̯͖̘͒̓̒͆̎̋̆͌͌̿̾̑̀̑̄͐̈́͑̒͗̔͋̾̿̐͑͂͊͐͆̿͑͐͗̐̑̈́̅́̍̋̎̃͂̌̃͘͘͘͘͘̕͠͠0̶̨̨̧̨̢̪͙̩̜̩̟͍̮̟̪̙͚̭̭͇̲̹̟̳͙͇̥̗̭̹̺̥͇̮̞͙̹͎̍̃̎̊̐̎͜͜͜1̸̡̨̡̢̢̧̨̠̝͉̤̹̺̠͕̹̬̝̳̟̦͙͕̯̦̟̰͚̹͙͔̫͖̹̪̙̪̞̖̠͔́͗̓͜ͅͅ1̸̢̨̛̛͍̣̠̠̭̯͈̱͕̘̼͖͖͇̠̰̟̙̪̪̳͙̞̭͉͙̓̔̈́͌͑̌͑̉̈́́͌̍̿̀͌͂̎͊̎̇̌̆̒͊͒͆͊̆́͐̕͘̕͝͠͠ :robot:\n"
            elif r >= 1150: msg2 = "P̶̧̢̺̜̮̟̼͔͔̻̲̩͎̘̖̲̐͂̑͂͛́͑̍̊̓͌̀̃͛͊͑͋̑̽̀́̆̀̔͋̋̂̏͒̀̎̈̾͑̉̅͒̉͂̑͒̕̕̚̚͝͝͝͝͝͝͝ļ̴̡̩͓͙̪̫̥͇͈͈̪̭̣̲͇̥̪͍̫̼̟͙̱̟̤̩̬͇̬̝͇̞͆͆͆̓̾̎͌̈͆̾̅̀͐̄̇̈́̔̊́̾̈͗̊̏̊̀̀̕̚̕͜͝͝ͅe̵̡̢̨̢̨̧̨̛̛̗̪̟̼̘̤̻̭̮̙̼̞͙̲̗̟͔̠̲̦̯̖̪̪͖̱̳̼̺͎͎̬̜̤̣͍̩̫̱̪̮̰̗̲̫̾̀̀̍̈́͂͋̑͑̑͒̈́̊͊̑́̐̅̿̈́̎͗̀̔̍̔̋̍̄͊̑̆̀̏̏̈́̀̉̈̐̅̚͘͘͜͜͝͝ͅͅȧ̴̢̢̧̧̢̡̳͕̲͖̰͔̝͖̱̙͙̫̞͕̮̫̼̤̹͔̫̹͉͚̞̠̬͎̘̯̱̳̯̠̪̰͎̖̻̹̖̜̪̣͍͋̄̐̍̽̒̓̀̐̈́̚͜ͅͅs̷̢̨̡̡̢̛̛̙̫̮͙̤͎̗̭̯̭͚̖͕̰̜̱̘̥̝͖̺͇̳̥̆͒̽͒̓̅̀́̽͌͌͌͂̉͛̊͌̌̉̌̋̈̀̽̍̀̔̋̀̒͒̃̌̊̆̍̀͊̐̐̇̑̽̊͘̕̕͝ͅe̶̢̧̨̢̧̨̝̗̝̠͙̳̼̙̤͍̠͖̙̖̱̳̼̘͉͍̲̦͉̝̞̞̬̮̝̱̥̪̟̯̹̹̘͇̗̯͓̬͖͐̓͛͛̓̌̂͊̚͘͠ͅ ̴̧̢̩̪̥̺̼͙̺̱̞̩̞͕͇̰͔̙͎͈̼̠̮͓̬̺͍̥͍͙̰̮̹̔̈͒̋͂͋̇̿̀̓̏̋̋̅̓͘̚͜͠͝͝Ş̵̛̛͇̙̟̼̤̫̱͖͖̮̩̹̭̮̣̩̫̙̳̗̜͓̪̻̖͇̼͖̣̝̈̏̏̈́̍̍̃̓̒̾̎͐͗͂̑͐͆̃͐̎̽͂͆͊̐̀̎̂͗̀́̿̎̆̀̾́̃̃̌̒̍̓͌̉̍̕͘̕͝͠͝ͅp̵̡̧̙͈̗̟͚̳̱͔̳̺̟̤̞̰̺̫̤͙̜̩͚̹̰͎͚͕̭͕̀̈̈̉̎̔̇ͅͅa̷̢̧̢̧̨̙͔͇͈̭̥̦͖̭̲͎̥͈͚͖̟͓̱͚͉̰̣͍͉̰͇͔̖̲̖͙̫̰̜̯̦͆̌̋̂̀̓͊́̓̄̒̈́̓͌̅́́̀͑́͊̚̕͜ͅŗ̵̡̗̲͇̺̰̭͕̪̩͋̊̎̔͒͛̈́̿͊͂̂̏̑́̉́͒͌̑̎͐͊̒͂́̄̋́͋͂̅̅͗͊̕̚͘̕̕̚͘͠͠ͅķ̵̨̧̧̹̩͇̣͔̤̦͍͉̘̘̹̹̠̪̰͉̗̯̦̣̘͉̳̦̼̥͕̣̪̭̩̦̥͓̝̣̰͉̻̇̈́̾̈͊̈́͗̈́̈́̌̂̈́͒̏̐͆̀̔̿̉̅̈́̀̈́͌̌̈͊̐̂͒̓́̀͛̌͘̚͘͘̚͘͜͜͝͝͠͠ :robot:\n"
            elif r >= 1100: msg2 = "Į̵̨̡̧̧̢̧̧͈͍͓͎̻͓͚̼̭̬̺̠̺̘̰̬̖̥̘̪̞̠̟̦̪͕̺̙͍͈̭͚̫̤͕̪̖̩̲̜̈́̅̍͛̽̑̐͋̀̅͂̑͋̊͂̒̊̀̂͊̈́͆̃͌̂̆̓́̒̓̈̒̍̑̂̓̕͘͘̕̕̕͝͝ͅͅt̷̨͇̥͇̭̹̀̔́̉͗̃͂̀͗̐̐̈́̎̀͘͜ ̸̡̛̗̭̫̟̫̬͇̲̳̺̗̦̭̤̠̗͓̳̥͉̗̖̰͎̩̬͚̙̯͕̟̭̗̮̤̲̭̲͉̠̦̹͎̩̤̺̖͈̘̞͇͒̂͆͆͗̂͗͛̒̏͒́͛̏͂͋̿͊̽̊͊̂̋́̐͌̇̄͛̐̐̌͒̏̔̑́͐͐͘̕͜͜͝͝͝h̸̢̡͔̗͕̻͍͚̦̪͇̺̘̗̞̭͇̰̼̠̟͉̰̤̞̞͔͙̻̯̬̬̬͓̩̻͖̞͈̙̐̊̓͒̒́͊̓̆̀͑́̌̀̊̓̿̎͛̍̅̋̔́̆̓̎̊̊́̀̄̂̾̎̍̏̒͛̆̇̉͐̏̏̂̃̕̚͘̕̚͠͝ͅŭ̷̢̯̱̤͎̦̥̜͈̉̆̏̊̄̈́̾̍̇͗̈́̈́͑̑́͌́̊̂͂̈́̉̓̐̑̃̾̽̊̂̕̕͜͝͝͝r̴̡̢̫̪͎̜͉͕̹̼̞̭̥̖̼̤̻̥͈͇̓̓͊͂͑̐̉̂̍̈́̏̓͜͝ͅţ̵̛̩̮̝̼̲͚̩̼̖̫̖͔̪̘̫͍̗̭̦̪͒͐̆̔͛̋̑̒̄̓̏̃̎̓̈́͛̇͛͋͗̅̏̊́̿̐͐͌͑͐̎̏̀̏͐̔̊̎̆̽̓̀̄̌́͘͜͝͝͝ͅs̸̛͚̣͛̀́́̌͌̏͌̉̐̒͑͋̐̍̚̕͝ :robot:\n"
            elif r >= 1050: msg2 = "S̷̨̧̢̯̝̱̩̥̺̹̜̬̳̜̳̞̪̳̘̼͓̭͖̮̱͈̼̫̰̘̟̻̞͈̩͔̻̯̥̜͔̭̰̾͌̌̊̍͊͛̊̉̀͛̑̍͆̂̐̔̈̍̅̎̐͊̐̓͂̀͒̾̑̄͗͛̄͊̑̿̿̉́̉̌͋̂̕͜͜͝͠ͅͅţ̸̢̨̢̨̨̳̳̮͉̰͖͈͓͈̖̗̻̭̺̳̮̜͕͕͚̜͎̳͇̹̪̪̯͓̤͔͖͇̣̼̬̺͙̞͉͋͊͐͆̽͜͜ơ̵̡̨̧̰̫͔͓̘̗̺͚̺͓̠̹̤̻̟͖̮͎͎̰̦̤̥̘̹̼̗̭͓̻͈͔̱̈́̔͒͗̈͒̈́͛̎̋͛̌̏͂͂̊͊͊̓̏̈́̑̆͗͊̄̎͒̌̎̈́̀̆͑̒̾͌͂́͌̽̋̕̚̚̕͠͝͝͝͝ṕ̶̨͈̜̰̓̾̏̍̐̊̾̃͑̏̂̐̽̔͋̽̀̈́̍̾͊̑̃̽́̈́̚͜͠͠͝ ̴̛͍͙̺̳͚̖͉̝̜̦̘̥̭̤̹̂̈́̌̀̂͌̑̔͊̅̾͗̊̈͝ņ̵̧̢̳̣̥̙̭̭̖̖̲͓̦̗̩̝͉̦̣͉̬̗̙̘̪̲͖̜̟̫͓̖̦̣̩̝͙̫͈́̋̽͂̓͐͌̀̂̌̑̏͌̍̑̿̒̌͗̽͆͐̈́̆̅̋̆̽̍̅̅̃̑̈́̍̃͘͜͜͝ͅö̵͈́w̷̧̧̧̢̛̛̗̺̪͍̬̪͚͇͇̯͈͓̰̯̻̭̹̺̞̣͍͇̯̪̮̬̙͓̤̱̘̱͓̫̅̈̓͛͗̋̐̓̑̎́̓͆͒͂́̈́̈́͗́̌̌͂͊̄̊̈́̋͌́̓̌̒̑̆̐́̐͛̆̈́̓̓̚̚͝͠͝͝͝͠͝ͅͅͅ :robot: \n"
            elif r >= 1000: msg2 = "ReAcHiNg CrItIcAl :robot:\n"
            elif r >= 900: msg2 = "Will you spark soon? :skull:\n"
            elif r >= 600: msg2 = "**STOP HOARDING** :confounded:\n"
            elif r >= 350: msg2 = "What are you waiting for? :thinking:\n"
            elif r >= 300: msg2 = "Dickpick or e-sport pick? :smirk:\n"
            elif r >= 250: msg2 = "Almost! :blush: \n"
            elif r >= 220: msg2 = "One more month :thumbsup: \n"
            elif r >= 180: msg2 = "You are getting close :ok_hand: \n"
            elif r >= 150: msg2 = "Half-way done :relieved:\n"
            elif r >= 100: msg2 = "Stay strong :wink:\n"
            elif r >= 50: msg2 = "You better save these rolls :spy: \n"
            elif r >= 20: msg2 = "Start saving **NOW** :rage:\n"
            else: msg2 = "Pathetic :nauseated_face: \n"
            msg3 = "Next spark between " + str(spark_time_range[0].year) + "/" + str(spark_time_range[0].month) + "/" + str(spark_time_range[0].day) + " and " + str(spark_time_range[1].year) + "/" + str(spark_time_range[1].month) + "/" + str(spark_time_range[1].day)
            await ctx.send(embed=self.bot.buildEmbed(title=msg1, description=msg2, footer=msg3, color=self.color))
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
            emotes = {0:self.bot.getEmoteStr('SSR'), 1:self.bot.getEmoteStr('SR'), 2:self.bot.getEmoteStr('R')}
            msg = ""
            top = 15
            for key, value in sorted(ranking.items(), key = itemgetter(1), reverse = True):
                if i < top:
                    fr = math.floor(value)
                    msg += "**#" + str(i+1).ljust(2) + emotes.pop(i, "▪") + " " + guild.get_member(int(key)).display_name + "** with " + str(fr) + " roll"
                    if fr != 1: msg += "s"
                    msg += "\n"
                if key == str(ctx.message.author.id):
                    ar = i
                    if i >= top: break
                i += 1
                if i >= 100:
                    break
            if ar >= top: footer = "You are ranked #" + str(ar+1)
            elif ar == -1: footer = "You aren't ranked ▪ You need at least one roll to be ranked"
            else: footer = ""
            await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('crown') + " Spark ranking of " + guild.name, color=self.color, description=msg, footer=footer, thumbnail=guild.icon_url))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Sorry, something went wrong :bow:", footer=str(e)))
            await self.bot.sendError("rollRanking", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['diexil', 'nemo', 'killxil'])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def xil(self, ctx):
        """Bully Xil"""
        try:
            msg = random.choice(self.bot.specialstrings['xil'])
            await ctx.send(msg.format(ctx.message.author.guild.get_member(self.bot.ids['xil']).mention))
        except:
            pass

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def wawi(self, ctx):
        """Bully Wawi"""
        try:
            wawiuser = ctx.message.author.guild.get_member(self.bot.ids['wawi'])
            if wawiuser is None:
                return
            msg = random.choice(self.bot.specialstrings['wawi'])
            r = ctx.message.author.guild.get_role(self.bot.ids['wawi_role'])
            if r is not None: await ctx.send(msg.format(r.mention))
            else: await ctx.send(msg.format(wawiuser.mention))
        except:
            pass

    @commands.command(no_pm=True, cooldown_after_parsing=True, hidden=True, aliases=['yawn', 'mig', 'mizako', 'miza', 'xenn', 'rubbfish', 'rubb', 'snak', 'snakdol', 'xell', 'kins', 'pics', 'roli', 'fresh', 'scrub', 'scrubp', 'milk', 'chen', 'marie', 'kinssim', 'tori', 'leader', 'simova', 'simo', 'den', 'snacks', 'varuna'])
    @isDisabled()
    @commands.cooldown(3, 180, commands.BucketType.user)
    @commands.cooldown(1, 50, commands.BucketType.guild)
    async def selfping(self, ctx):
        """Bully trap"""
        try:
            if ctx.author.id == self.bot.ids['owner']: return
            guild = ctx.message.author.guild
            author = ctx.message.author
            ch = guild.text_channels
            chlist = [] # build a list of channels where is the author
            for c in ch:
                if c.permissions_for(guild.me).send_messages and author in c.members:
                    chlist.append(c)

            msg = author.mention # get the ping for the author
            n = random.randint(4, 6) # number between 4 and 6
            await self.bot.react(ctx, 'kmr') # reaction
            await asyncio.sleep(1) # wait one second
            for i in range(0, n):
                await random.choice(chlist).send(msg) # send the ping in a random channel
                await asyncio.sleep(1) # wait one second
        except:
            pass

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def quota(self, ctx):
        """Give you your GW quota for the day"""
        chance = random.randint(1, 50)
        hr = random.randint(0, 320000000)
        mr = random.randint(0, 4200)
        hc = [[250000000, 0.01], [150000000, 0.1], [80000000, 0.4], [45000000, 0.6]]
        mc = [[3500, 0.01], [2000, 0.1], [1400, 0.3], [800, 0.6]]
        h = 0
        m = 0
        for xh in hc:
            if hr >= xh[0]:
                d = hr - xh[0]
                hr = xh[0]
                h += d * xh[1]
        for xm in mc:
            if mr >= xm[0]:
                d = mr - xm[0]
                mr = xm[0]
                m += d * xm[1]
        h = int(h + hr + 2000000)
        m = int(m + mr + 100)
        if ctx.author.id == self.bot.ids['yawn']:
            await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " " + ctx.author.display_name + " is a bad boy", description="Your account is **restricted.**", thumbnail=ctx.author.avatar_url ,color=self.color))
            return
        elif chance == 3:
            await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " " + ctx.author.display_name + "'s daily quota", description="You got a **free leech pass**\nCongratulations", thumbnail=ctx.author.avatar_url ,color=self.color))
            return
        elif chance == 1:
            h = h * 35
            m = m * 51
        elif ctx.author.id == self.bot.ids['wawi'] or chance == 2:
            h = h // 140
            m = m // 60
        if ctx.author.id == self.bot.ids['chen']:
            if h >= 666666666: h = 666666666
            elif h >= 66666666: h = 66666666
            elif h >= 6666666: h = 6666666
            elif h >= 666666: h = 666666
            elif h >= 66666: h = 66666
            elif h >= 6666: h = 6666
            if m >= 66666: m = 66666
            elif m >= 6666: m = 6666
            elif m >= 666: m = 666
            elif m >= 66: m = 66
            else: m = 6
        msg = "**Honor:** {:,}\n**Meat:** {:,}".format(h, m)
        await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " " + ctx.author.display_name + "'s daily quota", description=msg, thumbnail=ctx.author.avatar_url ,color=self.color))

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

        msg = "**Rarity** ▪ "
        rare = seed % 3
        if rare == 0: msg += self.bot.getEmoteStr('SSR')
        elif rare == 1: msg += self.bot.getEmoteStr('SR')
        elif rare == 2: msg += self.bot.getEmoteStr('R')
        
        msg += "\n**Race** ▪ "
        r = (seed - 1) % 6
        if r == 0: msg += 'Human'
        elif r == 1: msg += 'Erun'
        elif r == 2: msg += 'Draph'
        elif r == 3: msg += 'Harvin'
        elif r == 4: msg += 'Primal'
        elif r == 5: msg += 'Unknown'
        
        msg += "\n**Element** ▪ "
        r = (seed - 3) % 6
        if r == 0: msg += self.bot.getEmoteStr('fire')
        elif r == 1: msg += self.bot.getEmoteStr('water')
        elif r == 2: msg += self.bot.getEmoteStr('earth')
        elif r == 3: msg += self.bot.getEmoteStr('wind')
        elif r == 4: msg += self.bot.getEmoteStr('light')
        elif r == 5: msg += self.bot.getEmoteStr('dark')
        
        msg += "\n**Rating** ▪ {0:.1f}".format(((seed % 41) * 0.1) + 6.0 - rare * 2.0)

        await ctx.send(embed=self.bot.buildEmbed(author={'name':ctx.author.display_name + "'s daily character", 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, color=self.color))