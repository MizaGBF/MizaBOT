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
        self.scratcher_loot = {
            100 : ['Siero Ticket'],
            300 : ['Sunlight Stone', 'Gold Brick'],
            450 : ['Damascus Ingot'],
            600 : ['Agni', 'Varuna', 'Titan', 'Zephyrus', 'Zeus', 'Hades', 'Shiva', 'Europa', 'Godsworn Alexiel', 'Grimnir', 'Lucifer', 'Bahamut', 'Michael', 'Gabriel', 'Uriel', 'Raphael', 'Metatron', 'Sariel', 'Belial'],
            400 : ['Murgleis', 'Benedia', 'Gambanteinn', 'Love Eternal', 'AK-4A', 'Reunion', 'Ichigo-Hitofuri', 'Taisai Spirit Bow', 'Unheil', 'Sky Ace', 'Ivory Ark', 'Blutgang', 'Eden', 'Parazonium', 'Ixaba', 'Blue Sphere', 'Certificus', 'Fallen Sword', 'Mirror-Blade Shard', 'Galilei\'s Insight', 'Purifying Thunderbolt', 'Vortex of the Void', 'Sacred Standard', 'Bab-el-Mandeb', 'Cute Ribbon', 'Kerak', 'Sunya', 'Fist of Destruction', 'Yahata\'s Naginata', 'Cerastes', 'World Ender', 'Ouroboros Prime'],
            8000 : ['Damascus Crystal', 'Intricacy Ring', 'Brimston Earrings', 'Permafrost Earrings', 'Brickearth Earrings', 'Jetstream Earrings', 'Sunbeam Earrings', 'Nightshade Earrings'],
            10600 : ['Crystals x3000', 'Gold Spellbook', 'Moonlight Stone', 'Gold Moon x2', 'Ultima Unit x3', 'Silver Centrum x5', 'Primeval Horn x3', 'Horn of Bahamut x4', 'Legendary Merit x5', 'Steel Brick'],
            22000: ['Lineage Ring x2', 'Coronation Ring x3', 'Silver Moon x5', 'Bronze Moon x10'],
            33000: ['Elixir x100', 'Soul Berry x300']
        }
        self.scratcher_thumb = {
            'Siero Ticket':'item/article/s/30041.jpg', 'Sunlight Stone':'item/evolution/s/20014.jpg', 'Gold Brick':'item/evolution/s/20004.jpg', 'Damascus Ingot':'item/evolution/s/20005.jpg','Agni':'summon/s/2040094000.jpg', 'Varuna':'summon/s/2040100000.jpg', 'Titan':'summon/s/2040084000.jpg', 'Zephyrus':'summon/s/2040098000.jpg', 'Zeus':'summon/s/2040080000.jpg', 'Hades':'summon/s/2040090000.jpg', 'Shiva':'summon/s/2040185000.jpg', 'Europa':'summon/s/2040225000.jpg', 'Godsworn Alexiel':'summon/s/2040205000.jpg', 'Grimnir':'summon/s/2040261000.jpg', 'Lucifer':'summon/s/2040056000.jpg', 'Bahamut':'summon/s/2040030000.jpg', 'Michael':'summon/s/2040306000.jpg', 'Gabriel':'summon/s/2040311000.jpg', 'Uriel':'summon/s/2040203000.jpg', 'Raphael':'summon/s/2040202000.jpg', 'Metatron':'summon/s/2040330000.jpg', 'Sariel':'summon/s/2040327000.jpg', 'Belial':'summon/s/2040347000.jpg', 'Murgleis':'weapon/s/1040004600.jpg', 'Benedia':'weapon/s/1040502500.jpg',  'Gambanteinn':'weapon/s/1040404300.jpg',  'Love Eternal':'weapon/s/1040105400.jpg',  'AK-4A':'weapon/s/1040004600.jpg',  'Reunion':'weapon/s/1040108200.jpg',  'Ichigo-Hitofuri':'weapon/s/1040910000.jpg',  'Taisai Spirit Bow':'weapon/s/1040708700.jpg',  'Unheil':'weapon/s/1040809100.jpg',  'Sky Ace':'weapon/s/1040911500.jpg',  'Ivory Ark':'weapon/s/1040112500.jpg',  'Blutgang':'weapon/s/1040008700.jpg',  'Eden':'weapon/s/1040207000.jpg',  'Parazonium':'weapon/s/1040108700.jpg',  'Ixaba':'weapon/s/1040906400.jpg',  'Blue Sphere':'weapon/s/1040410000.jpg',  'Certificus':'weapon/s/1040309000.jpg',  'Fallen Sword':'weapon/s/1040014300.jpg',  'Mirror-Blade Shard':'weapon/s/1040110600.jpg',  'Galilei\'s Insight':'weapon/s/1040211600.jpg',  'Purifying Thunderbolt':'weapon/s/1040709000.jpg',  'Vortex of the Void':'weapon/s/1040212700.jpg',  'Sacred Standard':'weapon/s/1040213400.jpg',  'Bab-el-Mandeb':'weapon/s/1040004600.jpg',  'Cute Ribbon':'weapon/s/1040605900.jpg',  'Kerak':'weapon/s/1040812000.jpg',  'Sunya':'weapon/s/1040811800.jpg',  'Fist of Destruction':'weapon/s/1040612700.jpg',  'Yahata\'s Naginata':'weapon/s/1040312900.jpg',  'Cerastes':'weapon/s/1040215300.jpg',  'World Ender':'weapon/s/1040020900.jpg',  'Ouroboros Prime':'weapon/s/1040418600.jpg', 'Crystals x3000':'item/normal/s/gem.jpg', 'Damascus Crystal':'item/article/s/203.jpg', 'Intricacy Ring':'item/npcaugment/s/3.jpg', 'Gold Spellbook':'item/evolution/s/20403.jpg', 'Moonlight Stone':'item/evolution/s/20013.jpg', 'Gold Moon x2':'item/article/s/30033.jpg', 'Ultima Unit x3':'item/article/s/138.jpg', 'Silver Centrum x5':'item/article/s/107.jpg', 'Primeval Horn x3':'item/article/s/79.jpg', 'Horn of Bahamut x4':'item/article/s/59.jpg', 'Legendary Merit x5':'item/article/s/2003.jpg', 'Steel Brick':'item/evolution/s/20003.jpg', 'Brimston Earrings':'item/npcaugment/s/11.jpg', 'Permafrost Earrings':'item/npcaugment/s/12.jpg', 'Brickearth Earrings':'item/npcaugment/s/13.jpg', 'Jetstream Earrings':'item/npcaugment/s/14.jpg', 'Sunbeam Earrings':'item/npcaugment/s/15.jpg', 'Nightshade Earrings':'item/npcaugment/s/16.jpg', 'Lineage Ring x2':'item/npcaugment/s/2.jpg', 'Coronation Ring x3':'item/npcaugment/s/1.jpg', 'Silver Moon x5':'item/article/s/30032.jpg', 'Bronze Moon x10':'item/article/s/30031.jpg', 'Elixir x100':'item/normal/s/2.jpg', 'Soul Berry x300':'item/normal/s/5.jpg'
        }
        # scratcher rate calcul
        self.scratcher_total = 0
        self.scratcher_total_rare = 0
        rare_divider = 'Crystals x3000'
        for r in self.scratcher_loot:
            if self.scratcher_loot[r][0] == rare_divider: self.scratcher_total_rare = self.scratcher_total
            self.scratcher_total += r * len(self.scratcher_loot[r])

    # used by the gacha games
    def getRoll(self, ssr, sr_mode = False): # return 0 for ssr, 1 for sr, 2 for r
        d = random.randint(1, 10000)
        if d < ssr: return 0
        elif (not sr_mode and d < 1500 + ssr) or sr_mode: return 1
        return 2

    async def checkGacha(self): # no exception check on purpose
        await (self.bot.get_cog('GBF_Access')).getCurrentGacha()
        if self.bot.gbfdata.get('rateup', None) is None: raise Exception()

    def getRollExtended(self, ssr, sr_mode = False): # use the real gacha, return 2 for ssr, 1 for sr, 0 for r
        try:
            rateups = []
            for rate in self.bot.gbfdata['rateup'][2]['list']:
                rateups.append(rate)
            l = len(rateups)
            if l <= 1: rateups = sorted(rateups, key=float)
            elif l <= 3: rateups = sorted(rateups, key=float)[1:]
            else: rateups = sorted(rateups, key=float)[2:]
        except:
            rateups = []
        d = random.randint(1, 100000) / 1000
        if d < ssr:
            r = 2
            if ssr != self.bot.gbfdata['rateup'][r]['rate']:
                d = d * (self.bot.gbfdata['rateup'][r]['rate'] / ssr)
        elif (not sr_mode and d < 15 + ssr) or sr_mode:
            r = 1
            d -= ssr
            while d >= 15: d -= 15
        else:
            r = 0
            d -= ssr + 15
        for rate in self.bot.gbfdata['rateup'][r]['list']:
            fr = float(rate)
            for item in self.bot.gbfdata['rateup'][r]['list'][rate]:
                if r == 2 and rate in rateups: last = "**" + item + "**"
                else: last = item
                if d < fr: return [r, last]
                d -= fr
        return [r, last]

    legfestWord = {"double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2"}
    notfestWord = {"normal", "x1", "3%", "gacha", "1"}
    def isLegfest(self, word):
        word = word.lower()
        s = self.bot.gbfdata.get('gachacontent', '') # check the real gacha
        if s is None or s.find("**Premium Gala**") == -1: isleg = False
        else: isleg = True
        if word not in self.notfestWord and (word in self.legfestWord or isleg): return 2 # 2 because the rates are doubled
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

    def tenDrawsExtended(self, rate, draw, mode = 0):
        result = [0, 0, 0, {}]
        x = 0
        while mode > 0 or (mode == 0 and x < draw):
            i = 0
            while i < 10:
                r = self.getRollExtended(rate, i == 9)
                result[r[0]] += 1
                if r[0] == 2: result[3][r[1]] = result[3].get(r[1], 0) + 1
                i += 1
            if mode == 1 and result[2] > 0: break # gachapin / mukku
            elif mode == 2 and result[2] >= 5: break # super mukku
            x += 1
        return result

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def single(self, ctx, double : str = ""):
        """Do a single roll
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        try:
            await self.checkGacha()
            r = self.getRollExtended(3*l)
            msg = "{} {}".format(self.bot.getEmote({0:'R', 1:'SR', 2:'SSR'}.get(r[0])), r[1])
            if r[0] == 2: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761969229095632916/3_s.png'])
            elif r[0] == 1: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png'
            else: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969231323070494/0_s.png'
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} did a single roll...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, image=crystal, color=self.color, footer=footer))
            await asyncio.sleep(5)
            await final_msg.edit(embed=self.bot.buildEmbed(author={'name':"{} did a single roll".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        except: # legacy mode
            r = self.getRoll(300*l)
            if r == 0: msg = "Luckshitter! It's a {}".format(self.bot.getEmote('SSR'))
            elif r == 1: msg = "It's a {}".format(self.bot.getEmote('SR'))
            else: msg = "It's a {}, too bad!".format(self.bot.getEmote('R'))
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} did a single roll".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        await self.bot.cleanMessage(ctx, final_msg, 25)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['memerolls'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def memeroll(self, ctx, double : str = ""):
        """Do single rolls until a SSR
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1".
        Add R at the end of the keyword to target rate up SSRs (example: doubleR, it's not compatible with the legacy mode)."""
        if len(double) > 0 and double[-1] in ['r', 'R']:
            rateup = True
            double = double[:-1]
        else: rateup = False
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        if rateup: footer += " - stopping at rate up"
        try:
            await self.checkGacha()
            result = [0, 0, 0]
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} is memerolling...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="0 {} ▫️ 0 {} ▫️ 0 {}".format(self.bot.getEmote('SSR'), self.bot.getEmote('SR'), self.bot.getEmote('R')), color=self.color, footer=footer))
            msg = ""
            while True:
                r = self.getRollExtended(3*l)
                result[r[0]] += 1
                msg = "{} {} ▫️ {} {} ▫️ {} {}\n" + "{} {}".format(self.bot.getEmote({0:'R', 1:'SR', 2:'SSR'}.get(r[0])), r[1])
                while rateup and (r[0] != 2 or not r[1].startswith('**')) and sum(result) % 5 != 0: # roll twice for slower modes if no rate up ssr
                    r = self.getRollExtended(3*l)
                    result[r[0]] += 1
                    msg += "\n{} {}".format(self.bot.getEmote({0:'R', 1:'SR', 2:'SSR'}.get(r[0])), r[1])
                msg = msg.format(result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'))
                if sum(result) == 300 or (r[0] == 2 and (not rateup or (rateup and r[1].startswith('**')))): msg += "\n**{:.2f}%** SSR rate".format(100*result[2]/sum(result))
                if sum(result) == 300: title = "sparked"
                elif r[0] == 2: title = "memerolled until a SSR"
                else: title = "is memerolling..."
                await final_msg.edit(embed=self.bot.buildEmbed(author={'name':"{} {}".format(ctx.author.display_name, title), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
                if sum(result) == 300 or (r[0] == 2 and (not rateup or (rateup and r[1].startswith('**')))): break
                await asyncio.sleep(0.5*l)
        except: # legacy mode
            result = [0, 0, 0]
            while True:
                r = self.getRoll(300*l)
                result[r] += 1
                if r == 0: break
            msg = "{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/(result[0]+result[1]+result[2]))
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} memerolled until a SSR".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        await self.bot.cleanMessage(ctx, final_msg, 25)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ten(self, ctx, double : str = ""):
        """Do ten gacha rolls
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        try:
            await self.checkGacha()
            hasSSR = False
            rolls = []
            while len(rolls) < 10:
                rolls.append(self.getRollExtended(3*l, len(rolls) == 9))
                if rolls[-1][0] == 2: hasSSR = True
            if hasSSR: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761969229095632916/3_s.png'])
            else: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png'
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} did ten rolls...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, image=crystal, color=self.color, footer=footer))
            await asyncio.sleep(5)
            for i in range(0, 11):
                msg = ""
                for j in range(0, i):
                    if j == 11: break
                    msg += "{} {} ".format(self.bot.getEmote({0:'R', 1:'SR', 2:'SSR'}.get(rolls[j][0])), rolls[j][1])
                    if j % 2 == 1: msg += "\n"
                for j in range(i, 10):
                    if j == 11: break
                    msg += '{}'.format(self.bot.getEmote('crystal{}'.format(rolls[j][0])))
                    if j % 2 == 1: msg += "\n"
                await asyncio.sleep(0.75)
                await final_msg.edit(embed=self.bot.buildEmbed(author={'name':"{} did ten rolls".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        except: #legacy mode
            msg = ""
            i = 0
            while i < 10:
                r = self.getRoll(300*l, i == 9)
                if i == 5: msg += '\n'
                if r == 0: msg += '{}'.format(self.bot.getEmote('SSR'))
                elif r == 1: msg += '{}'.format(self.bot.getEmote('SR'))
                else: msg += '{}'.format(self.bot.getEmote('R'))
                i += 1
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} did ten rolls".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        await self.bot.cleanMessage(ctx, final_msg, 25)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def spark(self, ctx, double : str = ""):
        """Do thirty times ten gacha rolls
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: base_rate = 6
        else: base_rate = 3
        footer = "{}% SSR rate".format(base_rate)
        try:
            await self.checkGacha()
            result = self.tenDrawsExtended(3*l, 30)
            rate = (100*result[2]/300)
            if rate >= base_rate * 1.2: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969229095632916/3_s.png'
            elif rate >= base_rate: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761969229095632916/3_s.png'])
            elif rate >= base_rate * 0.9: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png'
            else: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761976275706445844/1_s.png'
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} is sparking...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, image=crystal, color=self.color, footer=footer))
            await asyncio.sleep(5)
            msg = "{} {} ▫️ {} {} ▫️ {} {}\n{} ".format(result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'), self.bot.getEmote('SSR'))
            for i in result[3]:
                msg += i
                if result[3][i] > 1: msg += " x{}".format(result[3][i])
                msg += ", "
                if i is list(result[3])[-1]: msg = msg[:-2] + "\n**{:.2f}%** SSR rate".format(rate)
                await asyncio.sleep(0.75)
                await final_msg.edit(embed=self.bot.buildEmbed(author={'name':"{} sparked".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        except: #legacy mode
            result = self.tenDraws(300*l, 30)
            msg = "{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/300)
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} sparked".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        await self.bot.cleanMessage(ctx, final_msg, 30)

    async def genGachapin(self, mode):
        try:
            await self.checkGacha()
            return 0, self.tenDrawsExtended(3*mode, 0, 1)
        except: #legacy mode
            return 1, self.tenDraws(300*mode, 0, 1)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['frenzy'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def gachapin(self, ctx, double : str = ""):
        """Do ten rolls until you get a ssr
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        gtype, result = await self.genGachapin(l)
        if gtype == 0:
            count = sum(result[:3])
            msg = "Gachapin stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n{} ".format(count, result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'), self.bot.getEmote('SSR'))
            for i in result[3]:
                msg += i
                if result[3][i] > 1: msg += " x{}".format(result[3][i])
                msg += ", "
            if len(result[3]) > 0: msg = msg[:-2]
            msg += "\n**{:.2f}%** SSR rate".format(100*result[2]/count)
        elif gtype == 1: #legacy mode
            count = sum(result)
            msg = "Gachapin stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} rolled the Gachapin".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        await self.bot.cleanMessage(ctx, final_msg, 25)

    async def genMukku(self, rate, mode):
        try:
            await self.checkGacha()
            return 0, self.tenDrawsExtended(rate//100, 0, mode)
        except: #legacy mode
            return 1, self.tenDraws(rate, 0, mode)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mook'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def mukku(self, ctx, super : str = ""):
        """Do ten rolls until you get a ssr, 9% ssr rate
        You can add "super" for a 9% rate and 5 ssr mukku"""
        if super.lower() == "super":
            footer = "Super Mukku ▫️ 15% SSR Rate and at least 5 SSRs"
            rate = 1500
            mode = 2
        else:
            footer = "9% SSR rate"
            rate = 900
            mode = 1
        gtype, result = await self.genMukku(rate, mode)
        if gtype == 0:
            result = self.tenDrawsExtended(rate//100, 0, mode)
            count = sum(result[:3])
            msg = "Mukku stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n{} ".format(count, result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'), self.bot.getEmote('SSR'))
            for i in result[3]:
                msg += i
                if result[3][i] > 1: msg += " x{}".format(result[3][i])
                msg += ", "
            if len(result[3]) > 0: msg = msg[:-2]
            msg += "\n**{:.2f}%** SSR rate".format(100*result[2]/count)
        elif gtype == 1: #legacy mode
            count = sum(result)
            msg = "Mukku stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} rolled the Mukku".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        await self.bot.cleanMessage(ctx, final_msg, 25)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['scratcher'])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def scratch(self, ctx, mode : str = ""):
        """Imitate the GBF scratch game from Anniversary 2020"""
        message = None
        ct = self.bot.getJST()
        # settings
        fixedS = ct.replace(year=2021, month=3, day=19, hour=19, minute=0, second=0, microsecond=0) # beginning of good scratcher
        fixedE = fixedS.replace(day=20, hour=19) # end of good scratcher
        betterScratcher = False # if true, only good results possible
        # settings end
        footer = ""
        if ct >= fixedS and ct < fixedE:
            betterScratcher = True
        

        # user options
        if mode == "debug" and ctx.author.id == self.bot.ids['owner']:
            msg = "`$scratch` Debug Values\nTotal: {} (100%)\n".format(self.scratcher_total)
            for r in self.scratcher_loot:
                msg += "{} Tier: {} ({}%)\n".format(self.scratcher_loot[r][0], r * len(self.scratcher_loot[r]), ((10000 * r * len(self.scratcher_loot[r])) // self.scratcher_total) / 100)
            debug_msg = await ctx.reply(embed=self.bot.buildEmbed(title="Scratcher Debug", description=msg, color=self.color))
            await self.bot.cleanMessage(ctx, debug_msg, 30)
        elif mode == "rigged" and ctx.author.id == self.bot.ids['owner']:
            betterScratcher = True
            footer = "Debug mode"

        if random.randint(1, 10000) <= 1000:
            betterScratcher = True # to simulate the rare scratcher card thing, currently 10%
        if footer == "" and betterSratcher: footer = "Rare card"
        selected = {}
        nloot = random.randint(4, 5)
        last = 'Soul Berry x300'
        is_rare = False
        while len(selected) < nloot:
            n = self.scratcher_total
            if betterScratcher:
                while n > self.scratcher_total_rare: # force a rare, according to settings
                    n = random.randint(1, self.scratcher_total)
            elif len(selected) == 1:
                while n > self.scratcher_total_rare: # force a rare, for the salt
                    n = random.randint(1, self.scratcher_total)
            else:
                n = random.randint(1, self.scratcher_total)
            c = 0
            found = False
            for r in self.scratcher_loot:
                for item in self.scratcher_loot[r]:
                    if n <= c:
                        if item in selected:
                            n += r
                        else:
                            selected[item] = 0
                            if c < self.scratcher_total_rare: is_rare = True
                            found = True
                        break
                    else:
                        c += r
                if found: break
        
        # build the scratch grid
        hidden = "▄▄▄▄▄▄▄▄▄▄▄"
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
            if nofinal and grid[-1][0] == "":
                break
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
                message = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, footer=footer, fields=fields, color=self.color))
            else:
                await message.edit(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, footer=footer, fields=fields, color=self.color))
            await asyncio.sleep(1)
            # win sequence
            if win_flag:
                if win == "": # final scratch must happens
                    win = grid[-1][0]
                    msg += "*The Final scratch...*\n"
                    await message.edit(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, footer=footer, fields=fields, color=self.color))
                    await asyncio.sleep(2)
                msg += ":confetti_ball: :tada: **{}** :tada: :confetti_ball:".format(win)
                for i in range(0, 9): # update the grid
                    if i < 3: fields[i%3]['value'] = ''
                    c = pulled.get(grid[i][0], 0)
                    if grid[i][1] == False: fields[i%3]['value'] += "~~{}~~\n".format(grid[i][0])
                    elif c == 3: fields[i%3]['value'] += "**{}**\n".format(grid[i][0])
                    elif c == 2: fields[i%3]['value'] += "__{}__\n".format(grid[i][0])
                    else: fields[i%3]['value'] += "{}\n".format(grid[i][0])
                await message.edit(embed=self.bot.buildEmbed(author={'name':"{} scratched".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, footer=footer, fields=fields, thumbnail='http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/' + self.scratcher_thumb.get(win, ''), color=self.color))
                await self.bot.cleanMessage(ctx, message, 45)
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
                message = await ctx.reply(embed=self.bot.buildEmbed(author={'name':title, 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            else:
                await message.edit(embed=self.bot.buildEmbed(author={'name':title, 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            if game_over:
                await self.bot.cleanMessage(ctx, message, 45)
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
        roll = 0
        rps = ['rock', 'paper', 'scissor']
        ct = self.bot.getJST()
        # customization settings
        fixedS = ct.replace(year=2021, month=3, day=19, hour=19, minute=0, second=0, microsecond=0) # beginning of fixed rolls
        fixedE = fixedS.replace(day=20, hour=19) # end of fixed rolls
        forced3pc = True # force 3%
        forcedRollCount = 100 # number of rolls during fixed rolls
        enable200 = False # add 200 on wheel
        enableJanken = False
        maxJanken = 2 # number of RPS
        doubleMukku = True
        # settings end
        state = 0
        superFlag = False
        if ct >= fixedS and ct < fixedE:
            msg = "{} {} :confetti_ball: :tada: Guaranteed **{} 0 0** R O L L S :tada: :confetti_ball: {} {}\n".format(self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), forcedRollCount//100, self.bot.getEmote('crystal'), self.bot.getEmote('crystal'))
            roll = forcedRollCount
            superFlag = True
            if l == 2 and forced3pc:
                footer = "3% SSR rate ▪️ You won't get legfest rates, you fool"
                l = 1
            d = 0
            state = 1
        else:
            d = random.randint(1, 36000)
            if enable200 and d < 300:
                msg = "{} {} :confetti_ball: :tada: **2 0 0 R O L L S** :tada: :confetti_ball: {} {}\n".format(self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'))
                roll = 200
            elif d < 1500:
                msg = "**Gachapin Frenzy** :four_leaf_clover:\n"
                roll = -1
                state = 2
            elif d < 2000:
                msg = ":confetti_ball: :tada: **100** rolls!! :tada: :confetti_ball:\n"
                roll = 100
            elif d < 6200:
                msg = "**30** rolls! :clap:\n"
                roll = 30
            elif d < 18000:
                msg = "**20** rolls :open_mouth:\n"
                roll = 20
            else:
                msg = "**10** rolls :pensive:\n"
                roll = 10
        final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{} is spinning the Roulette".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        if not enableJanken and state < 2: state = 1
        running = True
        while running:
            await asyncio.sleep(2)
            if state == 0: # RPS
                if enableJanken and d >= 2000 and random.randint(0, 2) > 0:
                    a = 0
                    b = 0
                    while a == b:
                        a = random.randint(0, 2)
                        b = random.randint(0, 2)
                    msg += "You got **{}**, Gachapin got **{}**".format(rps[a], rps[b])
                    if (a == 1 and b == 0) or (a == 2 and b == 1) or (a == 0 and b == 2):
                        msg += " :thumbsup:\nYou **won** rock paper scissor, your rolls are **doubled** :confetti_ball:\n"
                        roll = roll * 2
                        if roll > (200 if enable200 else 100): roll = (200 if enable200 else 100)
                        maxJanken -= 1
                        if maxJanken == 0:
                            state = 1
                    else:
                        msg += " :pensive:\n"
                        state = 1
                else:
                    state = 1
            elif state == 1: # normal rolls
                try:
                    await self.checkGacha()
                    result = self.tenDrawsExtended(3*l, roll//10)
                    count = sum(result[:3])
                    rate = (100*result[2]/count)
                    msg += "{} {} ▫️ {} {} ▫️ {} {}\n".format(result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'))
                    if result[2] > 0:
                        msg += "{} ".format(self.bot.getEmote('SSR'))
                        for i in result[3]:
                            msg += i
                            if result[3][i] > 1: msg += " x{}".format(result[3][i])
                            if i is list(result[3])[-1]: msg += "\n**{:.2f}%** SSR rate\n\n".format(rate)
                            else: msg += ", "
                except: # legacy mode
                    count = sum(result)
                    result = self.tenDraws(300*l, roll//10)
                    msg += "{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n\n".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)
                if superFlag: state = 4
                else: running = False
            elif state == 2: # gachapin
                gtype, result = await self.genGachapin(l)
                if gtype == 0:
                    count = sum(result[:3])
                    msg += "Gachapin ▫️ **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n{} ".format(count, result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'), self.bot.getEmote('SSR'))
                    for i in result[3]:
                        msg += i
                        if result[3][i] > 1: msg += " x{}".format(result[3][i])
                        msg += ", "
                    if len(result[3]) > 0: msg = msg[:-2]
                    msg += "\n**{:.2f}%** SSR rate\n\n".format(100*result[2]/count)
                elif gtype == 1: #legacy mode
                    count = sum(result)
                    msg += "Gachapin ▫️ **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)
                if count == 10 and random.randint(1, 100) < 99: state = 3
                elif count == 20 and random.randint(1, 100) < 60: state = 3
                elif count == 30 and random.randint(1, 100) < 30: state = 3
                else: running = False
            elif state == 3:
                gtype, result = await self.genMukku(900, 1)
                if gtype == 0:
                    count = sum(result[:3])
                    msg += ":confetti_ball: Mukku ▫️ **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n{} ".format(count, result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'), self.bot.getEmote('SSR'))
                    for i in result[3]:
                        msg += i
                        if result[3][i] > 1: msg += " x{}".format(result[3][i])
                        msg += ", "
                    if len(result[3]) > 0: msg = msg[:-2]
                    msg += "\n**{:.2f}%** SSR rate\n\n".format(100*result[2]/count)
                elif gtype == 1: #legacy mode
                    count = sum(result)
                    msg += "\n:confetti_ball: Mukku ▫️ **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)
                if doubleMukku:
                    if random.randint(1, 100) < 25: pass
                    else: running = False
                    doubleMukku = False
                else:
                    running = False
            elif state == 4:
                gtype, result = await self.genMukku(1500, 2)
                if gtype == 0:
                    count = sum(result[:3])
                    msg += ":confetti_ball: **Super Mukku** ▫️ **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n{} ".format(count, result[2], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[0], self.bot.getEmote('R'), self.bot.getEmote('SSR'))
                    for i in result[3]:
                        msg += i
                        if result[3][i] > 1: msg += " x{}".format(result[3][i])
                        msg += ", "
                    if len(result[3]) > 0: msg = msg[:-2]
                    msg += "\n**{:.2f}%** SSR rate".format(100*result[2]/count)
                elif gtype == 1: #legacy mode
                    count = sum(result)
                    msg += ":confetti_ball: **Super Mukku** ▫️ **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)
                running = False

            await final_msg.edit(embed=self.bot.buildEmbed(author={'name':"{} spun the Roulette".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))

        await self.bot.cleanMessage(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def quota(self, ctx):
        """Give you your GW quota for the day"""
        if ctx.author.id in self.bot.ids.get('branded', []):
            await ctx.reply(embed=self.bot.buildEmbed(title="{} {} is a bad boy".format(self.bot.getEmote('gw'), ctx.author.display_name), description="Your account is **restricted.**", thumbnail=ctx.author.avatar_url, color=self.color))
            return

        h = random.randint(800, 4000)
        m = random.randint(70, 180)
        c = random.randint(1, 100)

        if ctx.author.id == self.bot.ids.get('wawi', -1):
            c = 12

        if c <= 3:
            c = random.randint(1, 110)
            if c <= 2:
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got the **Eternal Battlefield Pass** 🤖\nCongratulations!!!\nYou will now revive GW over and ovḛ̸̛̠͕̑̋͌̄̎̍͆̆͑̿͌̇̇̕r̸̛̗̥͆͂̒̀̈́͑̑̊͐̉̎̚̚͝ ̵̨̛͔͎͍̞̰̠́͛̒̊̊̀̃͘ư̷͎̤̥̜̘͈̪̬̅̑͂̂̀̃̀̃̅̊̏̎̚͜͝ͅņ̴̢̛̛̥̮͖͉̻̩͍̱̓̽̂̂͌́̃t̵̞̦̿͐̌͗͑̀͛̇̚͝͝ỉ̵͉͕̙͔̯̯͓̘̬̫͚̬̮̪͋̉͆̎̈́́͛̕͘̚͠ͅļ̸̧̨̛͖̹͕̭̝͉̣̜͉̘͙̪͙͔͔̫̟̹̞̪̦̼̻̘͙̮͕̜̼͉̦̜̰̙̬͎͚̝̩̥̪̖͇̖̲̣͎̖̤̥͖͇̟͎̿̊͗̿̈̊͗̆̈́͋͊̔͂̏̍̔̒̐͋̄̐̄̅̇͐̊̈́̐͛͑̌͛̔͗̈́͌̀͑̌̅̉́̔̇́̆̉͆̄̂͂̃̿̏̈͛̇̒͆͗̈́̀̃̕̕͘̚̚͘͘͠͠͠͝͝͠͝͝ͅͅ ̴̢̛̛̛̯̫̯͕̙͙͇͕͕̪̩̗̤̗̺̩̬̞̞͉̱̊̽̇̉̏̃̑̋̋̌̎̾́̉́͌̿̐̆̒̾̆͒͛͌́͒̄͗͊͑̈́̑̐̂̿̋̊͊̈́̃̋̀̀̈̏̅̍̈͆̊̋͋̀̽͑̉̈́͘͘̕̕͝y̷̧̧̨̢̧̮̭̝̦͙͈͉̜͈̳̰̯͔͓̘͚̳̭͎̳̯͈͓̣͕͙̳̭̱͍͎͖̋͊̀͋͘͘ơ̸̢̗̖̹̹͖̣̫̝̞̦̘̙̭̮͕̘̱̆͋̓͗̾͐̉̏̀͂̄̎̂̈́͌͑̅̆̉̈̒͆̈̈̊͐̔̓̀̿̓̈́͝͝͝͠͝u̶̡̧̡̧̨̧̡̡̢̢̢̪̯͙͍̱̦̠̗̹̼̠̳̣͉̞̩̹͕̫͔͚̬̭̗̳̗̫̥̞̰̘̖̞̤͖̳̮̙͎͎̗̙̳͙͖͓̪̱̞͖̠̣̮̘͍̱̥̹͎͎̦̬̹̼̜͕͙͖̫̝̰̯̜̹̬̯͚͕̰̪̼͓̞̫̖̘͙̞͖̺̩͓̹̘̙̫̩̲̻̪̠̞̺͚̫̰̠̼̖̬͔̗̮͙̱̬̩̮̟͓̫̭̲̘̤͎̱̓̊̇́̀̏̏̾̀̄̆̒̂͐̌͂̈̂̓͋̌̓͘̕̕̚͜͜͜͝ͅͅͅͅŗ̷̡̧̨̢̢̢̧̡̡̧̡̢̧̨̨̡̧̛̛̛̬͚̮̜̟̣̤͕̼̫̪̗̙͚͉̦̭̣͓̩̫̞͚̤͇̗̲̪͕̝͍͍̫̞̬̣̯̤̮͉̹̫̬͕̫̥̱̹̲͔͔̪̖̱͔̹͈͔̳͖̩͕͚͓̤̤̪̤̩̰̬͙̞͙̘̯̮̫͕͚̙̜̼̩̰̻̞̺͈̝̝̖͎̻̹̞̥̰̮̥̙̠͔͎̤̲͎͍̟̥̞̗̰͓͍̞̹͍̬͎̲̬̞͈͉̼̥̝͈̼̠̫̙͖̪̼̲̯̲̫̼̺̘̗̘͚̤͓̯̦̣̬͒̑̒́͑͊̍̿̉̇̓̒̅̎͌̈́̐̽͋̏̒͂̈̒̃̿̓̇̈̿̊̎̈́͐̒͂͊̿̈́̿̅̏̀͐͛̎̍͑͂̈́̃̇̀̈͋̾̔̈́̽͌̿̍̇̅̏̋̑̈́̾̊͐̉̊̅͑̀͊̽̂̈́̽̓͗́̄͆̄͑͒̈́́͋̏͊͋̒͗̆̋̌̈̀͑͗̽͂̄̌̕͘͘̚͘̕̕͜͜͜͜͜͜͜͠͝͝͝͝͝͝ͅͅͅ ̷̧̡̧̨̢̧̨̡̨̧̛̛̛̛̮̭͇̣͓̙̺͍̟̜̞̫̪̘̼̞̜̠͇̗̮͕̬̥͓͔͈̟̦͇̥̖̭̝̱̗̠̘̝̹̖͓̝͇̖̫̯̩̞̞̯̲̤̱̻̤͇̲͍͈͓͖̹̗̟̲̪̪̟̩͙̪̝̮̘̽̋̍́̔̊̍̈́͂̌̽͒̆͐͊̏̐͑͛̓̆̈́͌̂͒͆̔̅̓̽͊̅́̾̽̓̏̆̀̀͌̾̀͒̓̇̊̀̐͛̌̋̈͑̇́̂̆̽̈̕̕̚̚͜͠ͅͅͅͅḑ̶̛̛̯͓̠̖͎̭̞̫͑̋̄̄̈̽̎̊͛̽͌̾̋̔̽̔̀̀͐̿̈́̀̃͐͂͆̈̃͑̀̋̑͊̃̆̓̾̎̅̀̆̓̏͊̆̔̈̅͛̍̎̓̀͛͒́̐͆̂̋̋͛̆̈͐͂̏̊̏̏̓̿̔͆̓̽̂̅͆̔͑̔̈̾̈̽̂̃̋̈́̾̎̈́̂̓̃̒͐͆̌̍̀͗̈́̑̌̚̕̕̚͠͠͝ę̴̧̨̨̨̢̨̢̧̧̧̨̧̛̛̛̛̛̛̛̺̪̹̘͈̣͔̜͓̥̥̟͇̱͚͖̠͙͙̱̞̣̤͚̣̟̫̬̟͓̺͙̬͚̹͓̗̬̼͇͙̻͍̖̙̥̩͔̜͕̖͕͔͚̳͙̩͇͙̺͔̲̱̙͉̝̠̤̝̭̮̩̦͇̖̳̞̞̖͎̙͙̲̮̠̣͍̪͙̰̣͉̘͉̦̖̳̫͖͖̘̖̮̲̱̪͕̳̫̫̞̪̜̞̬͙͖͍͖̦͉̯̟̖͇̩͚͙͔̳̫͗̈́̒̎͂̇̀͒̈́̃͐̉͛̾̑̆̃͐̈́̉͒̇̓̏̀͌̐͌̅̓͐́̿͒̅͑̍̓̈́̉̊́̉̀̔̊̍̽͛͛͆̓̈͋̉͋̿̉́̋̈̓̐̈́̔̃͆͗͛̏́̀̑͋̀̽̔̓̎̒̆̌̐̈́̓͂̐̋͊̌͑̓̈́̊̿͋̈́́̃̏̓̉͛͆̂͐͗͗̾̅̌̾͌̈́͊͘̕̚̕̚̚̕͘̕͜͜͜͜͜͜͜͠͝͝͠͝͝͠ͅͅa̸̡͔̯͎̟͙̖̗͔̺̰͇͚̭̲̭͕̫̜͉̯͕̅̈͋̒͋͂̐̕ͅţ̶̡̨̢̢̡̡̡̨̢̡̧̨̢̛̥̭̞͈̼̖͙͇̝̳͇̞̬͎̲̙̰̙̱̳̟̣̗̫̣͉͖̪̩͙̲͇͙̫̘͖̖̜̝̦̥̟̜̠͔̠͎̭͔̘͓͚̩͇͙͎͎̰̘̟̳̪͖̠̪̦̦̫̞̟̗̹̹̤͓͍̜̯͔̼̱̮̹͎͖͍̲͎̠͉̟͈̠̦̯̲̼̥̱̬̜͙̘͕̣̳͇̞͓̝͈̼̞̻͚̘̩̟̩̖̼͍̯̘͉͔̤̘̥̦͑̒͗̅̉̾͗̾̓̈́̍̉̈́͛̀͊̋̀͐̏̈́̀̀̍̇̀̀̈́̃̀̅͛̅̈́̇̽̆̌̈̄͆̄̂͂̔͗͌͊̽̿́͑̒̾̑̊̿͗́̇̋̊̄̀̍̓̆͂̆̔̏̍̑̔̊̾̎̆͛͑̓͒̈̎͌̓͗̀̿̓̃̔̈́͗̃̓̽̓̉̀͛͂̿́̀̌͊̆̋̀̓̇́̔̓͆̋̊̀̋͑́̔́̌̒̾̂̎̋̈́́̀͗̈́̈́́̾̈́͑͋̇͒̀͋͆͗̾͐̆̈́͂͐̈̐̓̍̈́̈̅̓͐̚̚̚̚̕͘̕͘̚̚̚͘͜͜͜͜͜͜͝͠͠͠͝͠ͅͅḥ̴̨̧̧̢̧̢̢̛̛̙̱͚̺̬̖̮̪͈̟͉̦̪̘̰̺̳̱̲͔̲̮̦̦̪̪̲̠͓͎͇͕̯̥͉͍̱̥͓̲̤̫̳̠̝͖̺̙͖͎͙̠͓̺̗̝̩͍͕͎̞͕̤̻̰̘͇͕̟̹̳͇͈͇̳̳̞̗̣͖̙͓̼̬̯͚͎̮͚̳̰͙̙̟̊͆͒͆͌̂̈́̀́̽̿͌̓́̐̑͌͋͆͊͑͛͑̀̋͐̏͌̑̀͛͗̀́̈̀̓̽̇̐̋͊̅͑̊͒̈́̀̀̔̀̇͗̆͑̅̌̑̈́͌̒̅̌̓͋͂̀̍̈́͐̈́̆̐̈́̍͛͂̔̐̎͂̎̇͑̈́̈́̎̉̈́́̒̒̆̌̃̓̈́͂̽̓̆̋̈̂̽̆̓̔͗̓̀̄̈́̂̏͗̐̔͘̕͘͘͜͜͜͜͠͠͝͠͠͝͝͝͠͠͝ͅͅ", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 6:
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Slave Pass** 🤖\nCongratulations!!!\nCall your boss and take a day off now!", footer="Full Auto and Botting are forbidden", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 16:
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Chen Pass** 😈\nCongratulations!!!\nYour daily honor or meat count must be composed only of the digit 6.", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 21:
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Carry Pass** 😈\nDon't stop grinding, continue until your Crew gets the max rewards!", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 26:
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Relief Ace Pass** 😈\nPrepare to relieve carries of their 'stress' after the day!!!", footer="wuv wuv", thumbnail=ctx.author.avatar_url, color=self.color))
            else:
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Free Leech Pass** 👍\nCongratulations!!!", thumbnail=ctx.author.avatar_url, color=self.color))
            await self.bot.cleanMessage(ctx, final_msg, 40)
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

        final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="**Honor:** {:,}\n**Meat:** {:,}".format(h, m), thumbnail=ctx.author.avatar_url ,color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 40)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 7, commands.BucketType.user)
    async def character(self, ctx):
        """Generate a random GBF character"""
        seed = (ctx.author.id + int(datetime.utcnow().timestamp()) // 86400) % 4428
        rarity = ['SSR', 'SR', 'R']
        race = ['Human', 'Erun', 'Draph', 'Harvin', 'Primal', 'Other']
        element = ['fire', 'water', 'earth', 'wind', 'light', 'dark']

        final_msg = await ctx.reply(embed=self.bot.buildEmbed(author={'name':"{}'s daily character".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="**Rarity** ▫️ {}\n**Race** ▫️ {}\n**Element** ▫️ {}\n**Rating** ▫️ {:.1f}".format(self.bot.getEmote(rarity[seed % 3]), race[(seed - 1) % 6], self.bot.getEmote(element[(seed - 3) % 6]), ((seed % 41) * 0.1) + 6.0 - (seed % 3) * 1.5), inline=True, color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 30)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def xil(self, ctx):
        """Generate a random element for Xil"""
        g = random.Random()
        elems = ['fire', 'water', 'earth', 'wind', 'light', 'dark']
        g.seed(int((int(datetime.utcnow().timestamp()) // 86400) * (1.0 + 1.0/4.2)))
        e = g.choice(elems)

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Today, Xil's main element is", description="{} **{}**".format(self.bot.getEmote(e), e.capitalize()), color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 30)

    @commands.command(no_pm=True, hidden=True, cooldown_after_parsing=True, aliases=['leek', 'leaks', 'leeks'])
    async def leak(self, ctx):
        """Do nothing"""
        await self.bot.react(ctx.message, '✅') # white check mark