import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import math
import re
import sqlite3
import os
from bs4 import BeautifulSoup
from xml.sax import saxutils as su

class GBF_Utility(commands.Cog):
    """GBF related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x46fc46

    def startTasks(self):
        pass

    def isYou(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isServer(ctx, 'you_server')
        return commands.check(predicate)

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    def getMaintenanceStatus(self): # check the gbf maintenance status, empty string returned = no maintenance
        current_time = self.bot.getJST()
        msg = ""
        if self.bot.maintenance['state'] == True:
            if current_time < self.bot.maintenance['time']:
                d = self.bot.maintenance['time'] - current_time
                if self.bot.maintenance['duration'] == 0:
                    msg = "{} Maintenance starts in **{}**".format(self.bot.getEmote('cog'), self.bot.getTimedeltaStr(d, True))
                else:
                    msg = "{} Maintenance starts in **{}**, for **{} hour(s)**".format(self.bot.getEmote('cog'), self.bot.getTimedeltaStr(d, True), self.bot.maintenance['duration'])
            else:
                d = current_time - self.bot.maintenance['time']
                if self.bot.maintenance['duration'] <= 0:
                    msg = "{} Emergency maintenance on going".format(self.bot.getEmote('cog'))
                elif (d.seconds // 3600) >= self.bot.maintenance['duration']:
                    self.bot.maintenance = {"state" : False, "time" : None, "duration" : 0}
                    self.bot.savePending = True
                else:
                    e = self.bot.maintenance['time'] + timedelta(seconds=3600*self.bot.maintenance['duration'])
                    d = e - current_time
                    msg = "{} Maintenance ends in **{}**".format(self.bot.getEmote('cog'), self.bot.getTimedeltaStr(d, True))
        return msg

    # function to fix the case (for $wiki)
    def fixCase(self, term): # term is a string
        fixed = ""
        up = False
        if term.lower() == "and": # if it's just 'and', we don't don't fix anything and return a lowercase 'and'
            return "and"
        elif term.lower() == "of":
            return "of"
        elif term.lower() == "(sr)":
            return "(SR)"
        elif term.lower() == "(ssr)":
            return "(SSR)"
        elif term.lower() == "(r)":
            return "(R)"
        for i in range(0, len(term)): # for each character
            if term[i].isalpha(): # if letter
                if term[i].isupper(): # is uppercase
                    if not up: # we haven't encountered an uppercase letter
                        up = True
                        fixed += term[i] # save
                    else: # we have
                        fixed += term[i].lower() # make it lowercase and save
                elif term[i].islower(): # is lowercase
                    if not up: # we haven't encountered an uppercase letter
                        fixed += term[i].upper() # make it uppercase and save
                        up = True
                    else: # we have
                        fixed += term[i] # save
                else: # other characters
                    fixed += term[i] # we just save
            elif term[i] == "/" or term[i] == ":" or term[i] == "#" or term[i] == "-": # we reset the uppercase detection if we encounter those
                up = False
                fixed += term[i]
            else: # everything else,
                fixed += term[i] # we save
        return fixed # return the result

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gbfwiki'])
    @commands.cooldown(3, 4, commands.BucketType.guild)
    async def wiki(self, ctx, *terms : str):
        """Search the GBF wiki"""
        if len(terms) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Tell me what to search on the wiki", footer="wiki [search terms]", color=self.color))
        else:
            try:
                arr = []
                for s in terms:
                    arr.append(self.fixCase(s))
                sch = "_".join(arr)
                url = "https://gbf.wiki/" + sch
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as r:
                        if r.status != 200:
                            raise Exception("HTTP Error 404: Not Found")
                await ctx.send(url)
            except Exception as e:
                if str(e) != "HTTP Error 404: Not Found":
                    await self.bot.sendError("wiki", str(e))
                await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Click here to refine the search\nhttps://gbf.wiki/index.php?title=Special:Search&search={}".format(sch), color=self.color, footer=str(e)))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tweet'])
    @commands.cooldown(1, 2, commands.BucketType.default)
    async def twitter(self, ctx, term : str = ""):
        """Post a twitter account (Tweepy enhanced)
        If none is found and twitter is enabled, try to get the corresponding user.
        options: granblue_en, en, noel, channel, tv wawi, raidpic, pic, kmr, fkhr,
        kakage, hag, jk, hecate, hecate_mk2, gbfverification, gw, gamewith, anime,
        gbf, granblue"""
        registered = {
            'granblue_en' : ["granblue_en", "Welcome EOP"],
            'en' : ["granblue_en", "Welcome EOP"],
            'noel' : ["noel_gbf", "Japanese Granblue news"],
            'tv' : ["noel_gbf", "Japanese Granblue news"],
            'channel' : ["noel_gbf", "Japanese Granblue news"],
            'wawi' : ["wawigbf", "Subscribe: https://twitter.com/Wawi3313"],
            'raidpic' : ["twihelp_pic", "To grab Granblue raid artworks"],
            'pic' : ["twihelp_pic", "To grab Granblue raid artworks"],
            'kmr' : ["kimurayuito", "Give praise, for he has no equal"],
            'fkhr' : ["hiyopi", "The second in charge"],
            'kakage' : ["kakage0904", "Young JK inside"],
            'hag' : ["kakage0904", "Young JK inside"],
            'jk' : ["kakage0904", "Young JK inside"],
            'hecate' : ["hecate_mk2", "For nerds :nerd:"],
            'hecate_mk2' : ["hecate_mk2", "For nerds :nerd:"],
            'gbfverification' : ["hecate_mk2", "For nerds :nerd:"],
            'gw' : ["granblue_gw", ":nine: / :keycap_ten:"],
            'gamewith' : ["granblue_gw", ":nine: / :keycap_ten:"],
            'anime' : ["anime_gbf", ":u5408:"],
            'gbf' : ["granbluefantasy", "Official account"],
            'granblue' : ["granbluefantasy", "Official account"]
        }

        target = registered.get(term.lower(), None)
        pic = None
        user = None
        accepted = (target is not None)

        if target is None:
            user = self.bot.getTwitterUser(term.lower())
        else:
            user = self.bot.getTwitterUser(target[0])
        if user is not None:
            pic = user.profile_image_url.replace("normal", "bigger")
        else:
            pic = None

        if accepted:
            if user is None:
                await ctx.send(embed=self.bot.buildEmbed(title=target[0], url="https://twitter.com/{}".format(target[0]), description=target[1], thumbnail=pic, color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title=user.name, url="https://twitter.com/{}".format(target[0]), description=target[1], thumbnail=pic, color=self.color))
        elif user is None:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="`{}` not found".format(term), color=self.color))
        elif ctx.channel.is_nsfw():
            await ctx.send(embed=self.bot.buildEmbed(title=user.name, url="https://twitter.com/{}".format(user.screen_name), thumbnail=pic, color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="NSFW protection", description="Check at your own risk\n[{}](https://twitter.com/{})".format(user.name, user.screen_name), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    async def reddit(self, ctx):
        """Post a link to /r/Granblue_en
        You wouldn't dare, do you?"""
        await ctx.send(embed=self.bot.buildEmbed(title="/r/Granblue_en/", url="https://www.reddit.com/r/Granblue_en/", thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/581522602325966864/lTgz7Yx_6n8VZemjf54viYVZgFhW2GlB6dlpj1ZwKbo.png", description="Disgusting :nauseated_face:", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['leech'])
    async def leechlist(self, ctx):
        """Post a link to /gbfg/ leechlist collection"""
        await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ Leechlist", description=self.bot.strings["leechlist()"], thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/582191446182985734/unknown.png", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['time', 'st', 'reset', 'gbf'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def granblue(self, ctx):
        """Post various Granblue Fantasy informations"""
        current_time = self.bot.getJST()
        description = "{:} Current Time is **{:02d}:{:02d} JST**".format(self.bot.getEmote('clock'), current_time.hour, current_time.minute)

        if self.bot.gbfversion is not None:
            description += "\n{} Version is `{}` (`{}`)".format(self.bot.getEmote('cog'), self.bot.gbfversion, self.bot.versionToDateStr(self.bot.gbfversion))

        reset = current_time.replace(hour=5, minute=0, second=0, microsecond=0)
        if current_time.hour >= reset.hour:
            reset += timedelta(days=1)
        d = reset - current_time
        description += "\n{} Reset in **{}**".format(self.bot.getEmote('mark'), self.bot.getTimedeltaStr(d))

        id = str(ctx.message.author.guild.id)
        if id in self.bot.st:
            st1 = current_time.replace(hour=self.bot.st[id][0], minute=0, second=0, microsecond=0)
            st2 = st1.replace(hour=self.bot.st[id][1])

            if current_time.hour >= st1.hour:
                st1 += timedelta(days=1)
            if current_time.hour >= st2.hour:
                st2 += timedelta(days=1)

            d = st1 - current_time
            if d.seconds >= 82800: description += "\n{} Strike times in {} **On going** ".format(self.bot.getEmote('st'), self.bot.getEmote('1'))
            else: description += "\n{} Strike times in {} **{}** ".format(self.bot.getEmote('st'), self.bot.getEmote('1'), self.bot.getTimedeltaStr(d))
            d = st2 - current_time
            if d.seconds >= 82800: description += "{} **On going**".format(self.bot.getEmote('2'))
            else: description += "{} **{}**".format(self.bot.getEmote('2'), self.bot.getTimedeltaStr(d))

        try:
            buf = self.getMaintenanceStatus()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("maintenanceUpdate", str(e))

        try:
            cog = self.bot.get_cog('GBF_Access')
            if cog is not None:
                buf = await cog.getCurrentGacha()
                if len(buf) > 0:
                    description += "\n{} Current gacha ends in **{}**".format(self.bot.getEmote('SSR'), self.bot.getTimedeltaStr(buf[0], True))
                    if buf[0] != buf[1]:
                        description += " (Spark period ends in **{}**)".format(self.bot.getTimedeltaStr(buf[1], True))
        except Exception as e:
            await self.bot.sendError("getgachatime", str(e))

        try:
            buf = self.bot.get_cog('GuildWar').getGWState()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getgwstate", str(e))

        try:
            buf = self.bot.get_cog('GuildWar').getNextBuff(ctx)
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getnextbuff", str(e))

        await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['maint'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def maintenance(self, ctx):
        """Post GBF maintenance status"""
        try:
            description = self.getMaintenanceStatus()
            if len(description) > 0:
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="Granblue Fantasy", description="No maintenance in my memory", color=self.color))
        except Exception as e:
            await self.bot.sendError("getMaintenanceStatus", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['drive'])
    @isYou()
    async def gdrive(self, ctx):
        """Post the (You) google drive
        (You) server only"""
        if ctx.message.author.guild.id == self.bot.ids.get('you_server', -1):
            try:
                image = self.bot.get_guild(self.bot.ids['you_server']).icon_url
            except:
                image = ""
            await ctx.send(embed=self.bot.buildEmbed(title="(You) Public Google Drive", description=self.bot.strings["gdrive()"], thumbnail=image, color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I'm not permitted to post this link here", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['arcarum', 'arca', 'oracle', 'evoker', 'astra'])
    async def arcanum(self, ctx):
        """Post a link to my autistic Arcanum Sheet"""
        await ctx.send(embed=self.bot.buildEmbed(title="Arcanum Tracking Sheet", description=self.bot.strings["arcanum()"], thumbnail="http://game-a.granbluefantasy.jp/assets_en/img_low/sp/assets/item/article/s/250{:02d}.jpg".format(random.randint(1, 46)), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['sparktracker'])
    async def rollTracker(self, ctx):
        """Post a link to my autistic roll tracking Sheet"""
        await ctx.send(embed=self.bot.buildEmbed(title="{} GBF Roll Tracker".format(self.bot.getEmote('crystal')), description=self.bot.strings["rolltracker()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['charlist', 'asset'])
    @isYou()
    async def datamining(self, ctx):
        """Post a link to my autistic datamining Sheet"""
        await ctx.send(embed=self.bot.buildEmbed(title="Asset Datamining Sheet", description=self.bot.strings["datamining()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwskin', 'blueskin'])
    async def stayBlue(self, ctx):
        """Post a link to my autistic blue eternal outfit grinding Sheet"""
        await ctx.send(embed=self.bot.buildEmbed(title="5* Eternal Skin Farming Sheet", description=self.bot.strings["stayblue()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['soldier'])
    async def bullet(self, ctx):
        """Post a link to my bullet grind Sheet"""
        await ctx.send(embed=self.bot.buildEmbed(title="Bullet Grind Sheet", description=self.bot.strings["bullet()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gbfgcrew', 'gbfgpastebin'])
    async def pastebin(self, ctx):
        """Post a link to the /gbfg/ crew pastebin"""
        await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ Guild Pastebin", description=self.bot.strings["pastebin()"], thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/582191446182985734/unknown.png", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tracker'])
    async def dps(self, ctx):
        """Post the custom Combat tracker"""
        await ctx.send(embed=self.bot.buildEmbed(title="GBF Combat Tracker", description=self.bot.strings["dps()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['grid', 'pool'])
    async def motocal(self, ctx):
        """Post the motocal link"""
        await ctx.send(embed=self.bot.buildEmbed(title="(You) Motocal", description=self.bot.strings["motocal()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['raidfinder', 'python_raidfinder'])
    async def pyfinder(self, ctx):
        """Post the (You) python raidfinder"""
        await ctx.send(embed=self.bot.buildEmbed(title="(You) Python Raidfinder", description=self.bot.strings["pyfinder()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['ubhl', 'ubaha'])
    async def ubahahl(self, ctx):
        """Post a simple Ultimate Baha HL image guide"""
        await ctx.send(embed=self.bot.buildEmbed(title="Ultimate Bahamut HL", description=self.bot.strings["ubahahl() 1"], image=self.bot.strings["ubahahl() 2"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["christmas", "anniversary", "anniv", "summer"])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def stream(self, ctx, op : str = ""):
        """Post the stream text"""
        if len(self.bot.stream['content']) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="No event or stream available", color=self.color))
        elif op == "raw":
            await ctx.send('`' + str(self.bot.stream['content']) + '`')
        else:
            title = self.bot.stream['content'][0]
            msg = ""
            current_time = self.bot.getJST()
            if self.bot.stream['time'] is not None:
                if current_time < self.bot.stream['time']:
                    d = self.bot.stream['time'] - current_time
                    cd = "{}".format(self.bot.getTimedeltaStr(d, True))
                else:
                    cd = "On going!!"
            else:
                cd = ""
            for i in range(1, len(self.bot.stream['content'])):
                if cd != "" and self.bot.stream['content'][i].find('{}') != -1:
                    msg += self.bot.stream['content'][i].format(cd) + "\n"
                else:
                    msg += self.bot.stream['content'][i] + "\n"
            
            if cd != "" and title.find('{}') != -1:
                title = title.format(cd) + "\n"

            await ctx.send(embed=self.bot.buildEmbed(title=title, description=msg, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["event"])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def schedule(self, ctx, raw : str = ""):
        """Post the GBF schedule"""
        if len(self.bot.schedule) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="No schedule available", color=self.color))
        else:
            l = len(self.bot.schedule)
            l = l - (l%2) # need an even amount, skipping the last one if odd
            i = 0
            msg = ""
            while i < l:
                if raw == 'raw':
                    if i != 0: msg += ";"
                    else: msg += "`"
                    msg += "{};{}".format(self.bot.schedule[i], self.bot.schedule[i+1])
                elif l > 12: # enable or not emotes (I have 6 numbered emotes, so 6 field max aka 12 elements in my array)
                    msg += "{} ▫️ {}\n".format(self.bot.schedule[i], self.bot.schedule[i+1])
                else:
                    msg += "{} {} ▫️ {}\n".format(self.bot.getEmote(str((i//2)+1)), self.bot.schedule[i], self.bot.schedule[i+1])
                i += 2
            if raw == 'raw': msg += "`"
            await ctx.send(embed=self.bot.buildEmbed(title="🗓 Event Schedule {} {:%Y/%m/%d %H:%M} JST".format(self.bot.getEmote('clock'), self.bot.getJST()), url="https://twitter.com/granblue_en", color=self.color, description=msg))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tokens'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def token(self, ctx, tok : int):
        """Calculate how many GW box you get from X tokens"""
        try:
            if tok < 1 or tok > 9999999999: raise Exception()
            b = 0
            t = tok
            if tok >= 1600:
                tok -= 1600
                b += 1
            while b < 4 and tok >= 2400:
                tok -= 2400
                b += 1
            while b < 46 and tok >= 2000:
                tok -= 2000
                b += 1
            while b < 81 and tok >= 10000:
                tok -= 10000
                b += 1
            while tok >= 15000:
                tok -= 15000
                b += 1
            ex = math.ceil(t / 56.0)
            explus = math.ceil(t / 66.0)
            n90 = math.ceil(t / 83.0)
            n95 = math.ceil(t / 111.0)
            n100 = math.ceil(t / 168.0)
            n150 = math.ceil(t / 257.0)
            wanpan = math.ceil(t / 48.0)
            await ctx.send(embed=self.bot.buildEmbed(title="{} Token Calculator ▫️ {}".format(self.bot.getEmote('gw'), t), description="**{:,}** box(s) and **{:,}** leftover tokens\n**{:,}** EX (**{:,}** pots)\n**{:,}** EX+ (**{:,}** pots)\n**{:,}** NM90 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM95 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM150 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 join (**{:}** BP)".format(b, tok, ex, math.ceil(ex*30/75), explus, math.ceil(explus*30/75), n90, math.ceil(n90*30/75), n90*5, n95, math.ceil(n95*40/75), n95*10, n100, math.ceil(n100*50/75), n100*20, n150, math.ceil(n150*50/75), n150*20, wanpan, wanpan*3), color=self.color))
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid token number", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def box(self, ctx, box : int):
        """Calculate how many GW tokens you need"""
        try:
            if box < 1 or box > 999: raise Exception()
            t = 0
            b = box
            if box >= 1: t += 1600
            if box >= 2: t += 2400
            if box >= 3: t += 2400
            if box >= 4: t += 2400
            if box > 80:
                t += (box - 80) * 15000
                box = 80
            if box > 45:
                t += (box - 45) * 10000
                box = 45
            if box > 4:
                t += (box - 4) * 2000
            ex = math.ceil(t / 56.0)
            explus = math.ceil(t / 66.0)
            n90 = math.ceil(t / 83.0)
            n95 = math.ceil(t / 111.0)
            n100 = math.ceil(t / 168.0)
            n150 = math.ceil(t / 257.0)
            wanpan = math.ceil(t / 48.0)
            await ctx.send(embed=self.bot.buildEmbed(title="{} Token Calculator ▫️ {}".format(self.bot.getEmote('gw'), b), description="**{:,}** tokens needed\n\n**{:,}** EX (**{:,}** pots)\n**{:,}** EX+ (**{:,}** pots)\n**{:,}** NM90 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM95 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM150 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 join (**{:}** BP)".format(t, ex, math.ceil(ex*30/75), explus, math.ceil(explus*30/75), n90, math.ceil(n90*30/75), n90*5, n95, math.ceil(n95*40/75), n95*10, n100, math.ceil(n100*50/75), n100*20, n150, math.ceil(n150*50/75), n150*20, wanpan, wanpan*3), color=self.color))
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid box number", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def meat(self, ctx, meat : int):
        """Calculate how many GW honors you get"""
        try:
            if meat < 5 or meat > 100000: raise Exception()
            nm90 = meat // 5
            nm95 = meat // 10
            nm100 = meat // 20
            nm150 = meat // 20
            await ctx.send(embed=self.bot.buildEmbed(title="{} Meat Calculator ▫️ {}".format(self.bot.getEmote('gw'), meat), description="**{:,}** NM90 or **{:}** honors\n**{:,}** NM95 or **{:}** honors\n**{:}** NM100 or **{:}** honors\n**{:,}** NM150 or **{:}** honors\n".format(nm90, self.honorFormat(nm90*260000), nm95, self.honorFormat(nm95*910000), nm100, self.honorFormat(nm100*2650000), nm150, self.honorFormat(nm150*4100000)), color=self.color))
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid meat number", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def honor(self, ctx, target : int):
        """Calculate how many NM95 and 150 you need for your targeted honor"""
        try:
            if target < 10000: raise Exception()
            honor = [0, 0, 0]
            ex = 0
            meat_per_ex_average = 3
            meat = 0
            total_meat = 0
            nm = [0, 0]
            day_target = [target * 0.15, target * 0.35]
            meat_use = [10, 20]
            honor_per_nm = [910000, 4100000]

            for i in [1, 0]:
                daily = 0
                while daily < day_target[i]:
                    if meat < meat_use[i]:
                        meat += meat_per_ex_average
                        total_meat += meat_per_ex_average
                        ex += 1
                        daily += 75000
                        honor[0] += 75000
                    else:
                        meat -= meat_use[i]
                        nm[i] += 1
                        daily += honor_per_nm[i]
                        honor[i+1] += honor_per_nm[i]

            await ctx.send(embed=self.bot.buildEmbed(title="{} Honor Planning ▫️ {} honors".format(self.bot.getEmote('gw'), self.honorFormat(target)), description="Preliminaries & Interlude ▫️ **{:,}** meats (around **{:,}** EX+ and **{:}** honors)\nDay 1 and 2 total ▫️ **{:,}** NM95 (**{:}** honors)\nDay 3 and 4 total ▫️ **{:,}** NM150 (**{:}** honors)".format(math.ceil(total_meat*2), ex*2, self.honorFormat(honor[0]*2), nm[0]*2, self.honorFormat(honor[1]*2), nm[1]*2, self.honorFormat(honor[2]*2)), footer="Assuming {} meats / EX+ on average".format(meat_per_ex_average), color=self.color))
        except Exception:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid honor number", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['friday'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def premium(self, ctx):
        """Post the time to the next Premium Friday"""
        c = self.bot.getJST()
        d = c
        last = None
        searching = True
        thumbnail = "https://cdn.discordapp.com/attachments/354370895575515138/584025273079562240/unknown.png"
        while searching:
            if d.weekday() == 4:
                last = d
            d = d + timedelta(seconds=86400)
            if last is not None and d.month != last.month:
                if c == last:
                    beg = last.replace(hour=15, minute=00, second=00)
                    end = c.replace(hour=23, minute=59, second=59) + timedelta(days=2, seconds=1)
                    if c >= beg and c < end:
                        end = end - c
                        await ctx.send(embed=self.bot.buildEmbed(title="{} Premium Friday".format(self.bot.getEmote('clock')), description="Premium Friday ends in **{}**".format(self.bot.getTimedeltaStr(end, True)), url="http://game.granbluefantasy.jp", thumbnail=thumbnail, color=self.color))
                        return
                    elif c >= end:
                        pass
                    elif c < beg:
                        last = beg
                        searching = False
                else:
                    searching = False
        last = last.replace(hour=15, minute=00, second=00) - c
        await ctx.send(embed=self.bot.buildEmbed(title="{} Premium Friday".format(self.bot.getEmote('clock')), description="Premium Friday starts in **{}**".format(self.bot.getTimedeltaStr(last, True)),  url="http://game.granbluefantasy.jp", thumbnail=thumbnail, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['koregura', 'koregra'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def korekara(self, ctx):
        """Post the time to the next monthly dev post"""
        c = self.bot.getJST()
        if c.day == 1:
            if c.hour >= 12:
                target = datetime(year=c.year, month=c.month+1, day=1, hour=12, minute=0, second=0, microsecond=0)
            else:
                target = datetime(year=c.year, month=c.month, day=1, hour=12, minute=0, second=0, microsecond=0)
        else:
            if c.month == 12: target = datetime(year=c.year+1, month=1, day=1, hour=12, minute=0, second=0, microsecond=0)
            else: target = datetime(year=c.year, month=c.month+1, day=1, hour=12, minute=0, second=0, microsecond=0)
        delta = target - c
        await ctx.send(embed=self.bot.buildEmbed(title="{} Kore Kara".format(self.bot.getEmote('clock')), description="Release approximately in **{}**".format(self.bot.getTimedeltaStr(delta, True)),  url="https://granbluefantasy.jp/news/index.php", thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png", color=self.color))

    def getSkillUpValue(self, type, sl): # calculate what's needed to raise a weapon skill level from a given skill level. return a list containing two dicts: first one contains the summary, second contains the details
        use = {}
        total = {}
        if type == 0:
            if sl >= 5: use['{}'.format(self.bot.getEmote('SR'))] = sl
            else: use['{}'.format(self.bot.getEmote('R'))] = sl*4
            total = use
        elif type == 1:
            if sl >= 15:
                use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = sl // 3
                total['{}'.format(self.bot.getEmote('SSR'))] = use['{} **SL3**'.format(self.bot.getEmote('SSR'))]
                total['{}'.format(self.bot.getEmote('SR'))] = total['{}'.format(self.bot.getEmote('SSR'))] * 6
                if sl % 3 == 2:
                    use['{} **SL2**'.format(self.bot.getEmote('SSR'))] = 1
                    total['{}'.format(self.bot.getEmote('SSR'))] += 1
                    total['{}'.format(self.bot.getEmote('SR'))] += 2
                elif sl % 3 == 1:
                    use['{}'.format(self.bot.getEmote('SSR'))] = 1
                    total['{}'.format(self.bot.getEmote('SSR'))] += 1
            elif sl >= 12:
                use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SR'))] = 6
            elif sl == 11:
                use['{} **SL2**'.format(self.bot.getEmote('SSR'))] = 1
                use['{}'.format(self.bot.getEmote('SR'))] = 2
                total['{}'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SR'))] = 4
            elif sl >= 6:
                use['{} **SL2**'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SR'))] = 2
            elif sl == 5:
                use['{}'.format(self.bot.getEmote('SSR'))] = 1
                total = use
            else:
                use['{}'.format(self.bot.getEmote('SR'))] = sl * 2
                total = use
        elif type == 2:
            if sl == 19:
                use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = 10
                use['{} **SL2**'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SSR'))] = 11
                total['{}'.format(self.bot.getEmote('SR'))] = 62
            elif sl == 18:
                use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = 10
                total['{}'.format(self.bot.getEmote('SSR'))] = 10
                total['{}'.format(self.bot.getEmote('SR'))] = 60
            elif sl == 17:
                use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = 9
                use['{} **SL2**'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SSR'))] = 10
                total['{}'.format(self.bot.getEmote('SR'))] = 54
            elif sl == 16:
                use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = 9
                total['{}'.format(self.bot.getEmote('SSR'))] = 9
                total['{}'.format(self.bot.getEmote('SR'))] = 54
            elif sl == 15:
                use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = 8
                use['{} **SL2**'.format(self.bot.getEmote('SSR'))] = 1
                total['{}'.format(self.bot.getEmote('SSR'))] = 9
                total['{}'.format(self.bot.getEmote('SR'))] = 48
            else:
                sl3 = sl // 3
                total['{}'.format(self.bot.getEmote('SSR'))] = 0
                if sl3 > 0:
                    use['{} **SL3**'.format(self.bot.getEmote('SSR'))] = sl3
                    total['{}'.format(self.bot.getEmote('SSR'))] += sl3
                    total['{}'.format(self.bot.getEmote('SR'))] = sl3 * 6
                if sl % 3 == 2:
                    use['{} **SL2**'.format(self.bot.getEmote('SSR'))] = 1
                    total['{}'.format(self.bot.getEmote('SSR'))] += 2
                    total['{}'.format(self.bot.getEmote('SR'))] = 2 + total.get('{}'.format(self.bot.getEmote('SR')), 0)
                elif sl % 3 == 1:
                    use['{}'.format(self.bot.getEmote('SSR'))] = 1
                    total['{}'.format(self.bot.getEmote('SSR'))] += 1
        return [use, total]

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['sl', 'skillup'])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def skillLevel(self, ctx, type : str, current : int, next : int = -1):
        """Calculate what you need for skill up
        type: sr, ssr, magna, omega, astral, ex, xeno, bahamut, baha, ultima, serap, seraphic, draconic, draco, opus
        current: your weapon current skill level
        next: your targeted skill level"""
        types = {'sr':0, 'ssr':1, 'magna':1, 'omega':1, 'astral':1, 'ex':1, 'xeno':1, 'bahamut':2, 'baha':2, 'ultima':2, 'seraph':2, 'seraphic':2, 'draconic':2, 'draco':2, 'opus':2}
        type = type.lower()
        value = types.get(type, -1)
        if value == -1:
            value = 1
            type = 'ssr ({} was invalid)'.format(type)
        if next < current: next = current + 1
        if current < 1:
            await ctx.send(embed=self.bot.buildEmbed(title="Skill Level Calculator", description="Current level can't be lesser than 1", url="https://gbf.wiki/Raising_Weapon_Skills", color=self.color))
            return
        if current >= 20 or (current >= 15 and value == 0):
            await ctx.send(embed=self.bot.buildEmbed(title="Skill Level Calculator", description="Current level is too high", url="https://gbf.wiki/Raising_Weapon_Skills", color=self.color))
            return
        while next > 20 or (next > 15 and value == 0):
            next -= 1
        total = {}
        count = 0
        divide = next - current + 1
        if divide < 6: divide = 6
        else: divide = divide // 2
        fields = []
        while current < next: 
            if count % divide == 0: fields.append({'name':'Page {}'.format(self.bot.getEmote('{}'.format(len(fields)+1))), 'value':''})
            count += 1
            res = self.getSkillUpValue(value, current)
            current += 1
            fields[-1]['value'] += "To **SL{}**▫️".format(current)
            first = True
            for k in res[0]:
                if first: first = False
                else: fields[-1]['value'] += ", "
                fields[-1]['value'] += "{} {}".format(res[0][k], k)
            fields[-1]['value'] += "\n"
            # add total
            for k in res[1]:
                total[k] = total.get(k, 0) + res[1][k]
        msg = "**Total**▫️"
        first = True
        for k in total:
            if first: first = False
            else: msg += ", "
            msg += "{} {}".format(total[k], k)
        await ctx.send(embed=self.bot.buildEmbed(title="Skill Level Calculator", description=msg, url="https://gbf.wiki/Raising_Weapon_Skills", fields=fields, inline=True, footer="type: {}".format(type), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['cb'])
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def chainburst(self, ctx):
        """Give the Battle 2.0 chain burst gain"""
        await ctx.send(embed=self.bot.buildEmbed(title="v2.0 Chain Burst", description="1 ▫️ **10%**\n2 ▫️ **23%**\n3 ▫️ **36%**\n4 ▫️ **50%**\n5 ▫️ **60%**", url="https://gbf.wiki/Battle_System_2.0#Chain_Burst", footer="chain size x 10 + chain size bonus", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["doom", "doompost", "magnafest", "magnafes", "campaign", "brick", "bar", "sunlight", "stone", "suptix", "surprise", "evolite", "fugdidmagnafeststart"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def deadgame(self, ctx):
        """Give the time elapsed of various GBF related releases"""
        msg = ""
        wiki_checks = [["Category:Campaign", "<td>(\d+ days)<\/td>\s*<td>Time since last campaign<\/td>"], ["Surprise_Special_Draw_Set", "<td>(\d+ days)<\/td>\s*<td>Time since last ticket<\/td>"], ["Damascus_Ingot", "<td>(\d+ days)<\/td>\s*<td style=\"text-align: left;\">Time since last brick<\/td>"], ["Gold_Brick", "<td>(\d+ days)<\/td>\s*<td style=\"text-align: center;\">\?\?\?<\/td>\s*<td style=\"text-align: left;\">Time since last brick<\/td>"], ["Sunlight_Stone", "<td>(\d+ days)<\/td>\s*<td style=\"text-align: left;\">Time since last stone<\/td>"], ["Sephira_Evolite", "<td>(\d+ days)<\/td>\s*<td style=\"text-align: center;\">\?\?\?<\/td>\s*<td style=\"text-align: left;\">Time since last evolite<\/td>"]]
        for w in wiki_checks:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://gbf.wiki/{}".format(w[0])) as r:
                    if r.status == 200:
                        m = re.search(w[1], await r.text())
                        if m:
                            msg += "**{}** since the last {}\n".format(m.group(1), w[0].replace("_", " ").replace("Category:", ""))

        if msg != "":
            await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Unavailable", color=self.color))