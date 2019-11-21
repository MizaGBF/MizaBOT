import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import math

class GBF_Utility(commands.Cog):
    """GBF related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x46fc46

    def startTasks(self):
        self.bot.runTask('maintenance', self.maintenancetask)

    async def maintenancetask(self): # gbf emergency maintenance detection
        await asyncio.sleep(3)
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="maintenancetask() started", timestamp=datetime.utcnow()))
        while True:
            try:
                if self.checkMaintenance():
                    if self.bot.maintenance['duration'] == 0: # check if infinite maintenance
                        req = await self.requestGBF()
                        if req[0].status == 200 and req[1].find("The app is now undergoing") == -1:
                            await self.bot.send('debug', embed=self.bot.buildEmbed(title="Emergency maintenance detected", timestamp=datetime.utcnow(), color=self.color))
                            c = self.bot.getJST()
                            self.bot.maintenance = {"state" : False, "time" : None, "duration" : 0}
                            self.bot.savePending = True
                        await asyncio.sleep(500)
                else:
                    req = await self.requestGBF()
                    if req[0].status == 200 and req[1].find("The app is now undergoing") != -1 and req[1].find("Starts: ") == -1:
                        await self.bot.send('debug', embed=self.bot.buildEmbed(title="Emergency maintenance detected", timestamp=datetime.utcnow(), color=self.color))
                        c = self.bot.getJST()
                        self.bot.maintenance['time'] = c
                        self.bot.maintenance['duration'] = 0
                        self.bot.maintenance['state'] = True
                        self.bot.savePending = True
                        await asyncio.sleep(100)
            except asyncio.CancelledError:
                await self.bot.sendError('maintenancetask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('maintenancetask', str(e))
            await asyncio.sleep(random.randint(30, 45))

    def isYou(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isYouServer(ctx)
        return commands.check(predicate)

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    async def requestGBF(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("http://game.granbluefantasy.jp") as r:
                s = await r.read()
                s = s.decode('utf-8')
                return [r, s]
        raise Exception("Failed to request: http://game.granbluefantasy.jp")

    def maintenanceUpdate(self): # check the gbf maintenance status, empty string returned = no maintenance
        current_time = self.bot.getJST()
        msg = ""
        if self.bot.maintenance['state'] == True:
            if current_time < self.bot.maintenance['time']:
                d = self.bot.maintenance['time'] - current_time
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

    def checkMaintenance(self):
        msg = self.maintenanceUpdate()
        return (msg.find("ends in") != -1 or msg.find("Emergency maintenance on going") != -1)

    # function to fix the case (for $wiki)
    def fixCase(self, term): # term is a string
        fixed = ""
        up = False
        if term.lower() == "and": # if it's just 'and', we don't don't fix anything and return a lowercase 'and'
            return "and"
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
                else: # error case
                    fixed += term[i] # we just save
            elif term[i] == "/" or term[i] == ":" or term[i] == "#": # we reset the uppercase detection if we encounter those
                up = False
                fixed += term[i]
            else: # everything else,
                fixed += term[i] # we save
        return fixed # return the result

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gbfwiki'])
    @commands.cooldown(3, 4, commands.BucketType.guild)
    async def wiki(self, ctx, *terms : str):
        """Search the GBF wiki
        add embed at the end to show the discord preview"""
        if len(terms) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Tell me what to search on the wiki", footer="wiki [search] [embed]", color=self.color))
        else:
            try:
                arr = []
                for s in terms:
                    arr.append(self.fixCase(s))
                if len(terms) >= 2 and terms[-1] == "embed":
                    sch = "_".join(arr[:-1])
                    terms = terms[:-1]
                    full = True
                else:
                    sch = "_".join(arr)
                    full = False
                url = "https://gbf.wiki/" + sch
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as r:
                        if r.status != 200:
                            raise Exception("HTTP Error 404: Not Found")
                if full: await ctx.send("Click here :point_right: {}".format(url))
                else: await ctx.send(embed=self.bot.buildEmbed(title="{} search result".format(" ".join(terms)), description="Click here :point_right: {}".format(url), color=self.color))
            except Exception as e:
                if str(e) != "HTTP Error 404: Not Found":
                    await self.bot.sendError("wiki", str(e))
                await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Click here to refine the search\nhttps://gbf.wiki/index.php?title=Special:Search&search={}".format(" ".join(terms)), color=self.color, footer=str(e)))


    wiki_options = {'en':0, 'english':0, 'noel':1, 'radio':1, 'channel':1, 'tv':1, 'wawi':2, 'raidpic':3, 'pic':3, 'kmr':4, 'fkhr':5, 'kakage':6,
        'hag':6, 'jk':6, 'hecate':7, 'hecate_mk2':7, 'gbfverification':7, 'chiaking':8, 'gw':9, 'gamewith':9, 'anime':10, 'gbf':11, 'granblue':11}
    wiki_accounts = [["Welcome EOP", "granblue_en"], ["GBF TV news and more", "noel_gbf"], ["Subscribe: https://twitter.com/Wawi3313", "WawiGbf"], ["To grab raid artworks", "twihelp_pic"], ["Give praise, for he has no equal", "kimurayuito"], ["The second in charge", "hiyopi"], ["Young JK inside", "kakage0904"], ["For nerds :nerd:", "hecate_mk2"], [":relaxed: :eggplant:", "chiaking58"], [":nine: / :keycap_ten:", "granblue_gw"], [":u5408:", "anime_gbf"], ["Official account", "granbluefantasy"]]
    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tweet'])
    @commands.cooldown(1, 2, commands.BucketType.default)
    async def twitter(self, ctx, term : str = ""):
        """Post a gbf related twitter account
        default is the official account
        options: en, english, noel, radio, channel, tv wawi, raidpic, pic, kmr, fkhr,
        kakage, hag, jk, hecate, hecate_mk2, gbfverification, chiaking, gw, gamewith, anime,
        gbf, granblue"""
        terml = term.lower()
        url = "https://twitter.com/{}"
        pic = "https://twitter.com/{}/profile_image?size=bigger"
        try:
            a = self.wiki_accounts[self.wiki_options[terml]]
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="`{}` isn't in my database".format(term), footer="Use the help for the full list", color=self.color))
            return

        # get avatar url
        async with aiohttp.ClientSession() as session:
            async with session.get(pic.format(a[1]), allow_redirects=False) as r:
                if r.status == 302:
                    pic = r.headers['location']
                else:
                    pic = ""

        url = url.format(a[1])
        await ctx.send(embed=self.bot.buildEmbed(title=url, url=url, description=a[0], thumbnail=pic, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    async def reddit(self, ctx):
        """Post a link to /r/Granblue_en
        You wouldn't dare, do you?"""
        await ctx.send(embed=self.bot.buildEmbed(title="/r/Granblue_en/", url="https://www.reddit.com/r/Granblue_en/", thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/581522602325966864/lTgz7Yx_6n8VZemjf54viYVZgFhW2GlB6dlpj1ZwKbo.png", description="Disgusting :nauseated_face:", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['leech'])
    async def leechlist(self, ctx):
        """Post a link to /gbfg/ leechlist collection"""
        await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ Leechlist", description=self.bot.strings["leechlist()"], thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/582191446182985734/unknown.png", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, name='time', aliases=['st', 'reset'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def _time(self, ctx):
        """Post remaining time to next reset and strike times (if set)
        Also maintenance and gw times if set"""
        current_time = self.bot.getJST()

        title = "{} Current Time: {:02d}:{:02d}".format(self.bot.getEmote('clock'), current_time.hour, current_time.minute)

        reset = current_time.replace(hour=5, minute=0, second=0, microsecond=0)
        if current_time.hour >= reset.hour:
            reset += timedelta(days=1)
        d = reset - current_time
        description = "{} Reset in **{}**".format(self.bot.getEmote('mark'), self.bot.getTimedeltaStr(d))

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
            buf = self.maintenanceUpdate()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("maintenanceUpdate", str(e))

        try:
            cog = self.bot.get_cog('Baguette')
            buf = await cog.getGachatime()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getgachatime", str(e))

        try:
            buf = self.bot.get_cog('GW').getGWState()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getgwstate", str(e))

        try:
            buf = self.bot.get_cog('GW').getNextBuff(ctx)
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getnextbuff", str(e))

        await ctx.send(embed=self.bot.buildEmbed(title=title, url="http://game.granbluefantasy.jp/", description=description, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['maint'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def maintenance(self, ctx):
        """Post GBF maintenance status"""
        try:
            description = self.maintenanceUpdate()
            if len(description) > 0:
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="Granblue Fantasy", description="No maintenance in my memory", color=self.color))
        except Exception as e:
            await self.bot.sendError("maintenanceUpdate", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    async def gacha(self, ctx):
        """Post when the current gacha end"""
        try:
            cog = self.bot.get_cog('Baguette')
            description = await cog.getGachatime()
            if len(description) > 0:
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))
        except Exception as e:
            await self.bot.sendError("getgachatime", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rateup'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def banner(self, ctx, jp : str = ""):
        """Post the current gacha rate up
        add 'jp' for the japanese image"""
        try:
            cog = self.bot.get_cog('Baguette')
            buf = await cog.getGachabanner(jp)
            if len(buf) > 0:
                image_index = buf.find("\nhttp")
                if image_index != -1:
                    image = buf.splitlines()[-1]
                    description = buf[0:image_index]
                else:
                    description = buf
                    image = ""
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, image=image, color=self.color))
        except Exception as e:
            await self.bot.sendError("getgachabanner", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['ticket'])
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def upcoming(self, ctx, jp : str = ""):
        """Post the upcoming gacha(s)"""
        try:
            cog = self.bot.get_cog('Baguette')
            tickets = cog.getLatestTicket()
            l = len(tickets)
            if l > 0:
                await ctx.send(embed=self.bot.buildEmbed(title="Last Gacha update", description="New: {}".format(l), thumbnail=tickets[0], color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="No new upcoming gacha", color=self.color))
        except Exception as e:
            await self.bot.sendError("getlatestticket", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['drive'])
    @isYou()
    async def gdrive(self, ctx):
        """Post the (You) google drive
        (You) server only"""
        if ctx.message.author.guild.id == self.bot.ids['you_server']:
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

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["christmas", "anniversary", "xmas", "anniv", "summer"])
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
                    msg += "{} ▪ {}\n".format(self.bot.schedule[i], self.bot.schedule[i+1])
                else:
                    msg += "{} {} ▪ {}\n".format(self.bot.getEmote(str((i//2)+1)), self.bot.schedule[i], self.bot.schedule[i+1])
                i += 2
            if raw == 'raw': msg += "`"
            await ctx.send(embed=self.bot.buildEmbed(title="🗓 Event Schedule {} {:%Y/%m/%d %H:%M} JST".format(self.bot.getEmote('clock'), self.bot.getJST()), url="https://twitter.com/granblue_en", color=self.color, description=msg))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tokens', 'box'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def token(self, ctx, box : int):
        """Calculate how many tokens you need"""
        try:
            if box < 1 or box > 999: raise Exception()
            t = 0
            b = box
            if box >= 1: t += 1600
            if box >= 2: t += 2400
            if box >= 3: t += 2400
            if box >= 4: t += 2400
            if box > 44:
                t += (box - 44) * 6000
                box = 44
            if box > 4:
                t += (box - 4) * 2000
            ex = math.ceil(t / 56.0)
            explus = math.ceil(t / 66.0)
            n90 = math.ceil(t / 83.0)
            n95 = math.ceil(t / 111.0)
            n100 = math.ceil(t / 168.0)
            n150 = math.ceil(t / 220.0)
            wanpan = math.ceil(t / 48.0)
            await ctx.send(embed=self.bot.buildEmbed(title="{} Token Calculator".format(self.bot.getEmote('gw')), description="**{:,}** token(s) needed for **{:,}** box(s)\n\n**{:,}** EX host and MVP (**{:,}** AP)\n**{:,}** EX+ host and MVP (**{:,}** AP)\n**{:,}** NM90 host and MVP (**{:,}** AP, **{:,}** meats)\n**{:,}** NM95 host and MVP (**{:,}** AP, **{:,}** meats)\n**{:,}** NM100 host and MVP (**{:,}** AP, **{:,}** meats)\n**{:,}** NM150 host and MVP (**{:,}** AP, **{:,}** meats)\n**{:,}** NM100 wanpan (**{:}** BP)".format(t, b, ex, ex*30, explus, explus*30, n90, n90*30, n90*5, n95, n95*40, n95*10, n100, n100*50, n100*20, n150, n150*50, n150*20, wanpan, wanpan*3), color=self.color))
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid box number", color=self.color))

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
            target = datetime(year=c.year, month=c.month+1, day=1, hour=12, minute=0, second=0, microsecond=0)
        delta = target - c
        await ctx.send(embed=self.bot.buildEmbed(title="{} Kore Kara".format(self.bot.getEmote('clock')), description="Release approximately in **{}**".format(self.bot.getTimedeltaStr(delta, True)),  url="https://granbluefantasy.jp/news/index.php", thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['sl', 'skillup'])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def skillLevel(self, ctx, type : str, level : int):
        """Calculate what you need for skill up
        type: sr, ssr, magna, omega, bahamut, baha, ultima, serap, seraphic, opus
        level: your weapon current level"""
        type = type.lower()
        try:
            if level < 1: raise Exception("Current level can't be negative")
            if type == "sr":
                if level >= 15: raise Exception("Can't skill up a {} weapon **SL{}**".format(self.bot.getEmote('SR'), level))
                if level >= 5:
                    msg = "**{}** {} to reach **SL{}**".format(level, self.bot.getEmote('SR'), level+1)
                else:
                    msg = "**{}** {} or **{}** {} to reach **SL{}**".format(level, self.bot.getEmote('SR'), level*4, self.bot.getEmote('R'), level+1)
            elif type in ["ssr", "magna", "omega"]:
                if level >= 20: raise Exception("Can't skill up a {} weapon **SL{}**".format(self.bot.getEmote('SSR'), level))
                if level >= 15: 
                    msg = "**{}** {} to reach **SL{}**".format(level, self.bot.getEmote('SSR'), level+1)
                elif level > 10: 
                    msg = "**2** {} and **{}** {} to reach **SL{}**".format(self.bot.getEmote('SSR'), (level-10)*2, self.bot.getEmote('SR'), level+1)
                elif level == 10: 
                    msg = "**2** {} to reach **SL{}**".format(self.bot.getEmote('SSR'), level+1)
                elif level > 5: 
                    msg = "**1** {} and **{}** {} to reach **SL{}**".format(self.bot.getEmote('SSR'), (level-5)*2, self.bot.getEmote('SR'), level+1)
                elif level == 5: 
                    msg = "**1** {} to reach **SL{}**".format(self.bot.getEmote('SSR'), level+1)
                else:
                    msg = "**{}** {} to reach **SL{}**".format(level*2, self.bot.getEmote('SR'), level+1)
            elif type in ["bahamut", "baha", "ultima", "seraph", "seraphic", "opus"]:
                if level >= 20: raise Exception("Can't skill up a {} weapon **SL{}**".format(self.bot.getEmote('SSR'), level))
                if level == 19: 
                    msg = "**32** {} or **8** {} SL4 to reach **SL{}**".format(self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), level+1)
                elif level == 18: 
                    msg = "**30** {} or **6** {} SL4 and **2** {} SL3 to reach **SL{}**".format(self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), level+1)
                elif level == 17: 
                    msg = "**29** {} or **5** {} SL4 and **3** {} SL3 to reach **SL{}**".format(self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), level+1)
                elif level == 16: 
                    msg = "**27** {} or **6** {} SL4 and **1** {} SL3 to reach **SL{}**".format(self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), level+1)
                elif level == 15: 
                    msg = "**25** {} or **4** {} SL4 and **3** {} SL3 to reach **SL{}**".format(self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), self.bot.getEmote('SSR'), level+1)
                else:
                    msg = "**" + str(level) + "** " + self.bot.getEmote('SSR') + " to reach **SL" + str(level+1) + "**"
                    msg = "**{}** {} to reach **SL{}**".format(level, self.bot.getEmote('SSR'), level+1)
            else:
                raise Exception("Unknown type `{}`".format(type))
            await ctx.send(embed=self.bot.buildEmbed(title="Skill Level Calculator", description=msg,  url="https://gbf.wiki/Raising_Weapon_Skills", color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Skill Level Calculator", description=str(e),  url="https://gbf.wiki/Raising_Weapon_Skills", color=self.color))


    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['arcaset'])
    @isAuthorized()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def aSet(self, ctx, *what : str):
        """Set your arcarum progress
        Input:
        - what you want to set/update (summon name, sephira, astra...)
        - followed by the new value (example: ssr3, sr2, oracle4 for a summon)
        Chain multiples with ; (example: tower sr3;temperance ssr4;sephira 30)"""
        types = {"justice ":0, "hanged man ":1, "the hanged man ":1, "death ":2, "temperance ":3, "the devil ":4, "devil ":4, "the tower ":5, "tower ":5, "the star ":6, "star ":6, "the moon ":7, "moon ":7, "the sun ":8, "sun ":8, "judgement ":9}
        sumsteps = {"none":0, "zero":0, "0":0, "":0, "sr0":1, "sr1":2, "sr2":3, "sr3":4, "ssr3":5, "ssr":5, "ssr4":6, "flb":6, "ssr5":7, "ulb":7, "oracle":8, "oracle0":8, "oracle1":9, "oracle2":10, "oracle3":11, "oracle4":12}

        parameters = " ".join(what)
        if parameters == "":
            await ctx.send(embed=self.bot.buildEmbed(title="Precise what you want to set", description="example string:\n`justice sr0;hanged man sr0;death sr0;temperance sr0;devil sr0;tower sr0;star sr0;moon sr0;sun sr0,judgement sr0;sephira 0;fire astra 0;water astra 0;earth astra 0;wind astra 0;light astra 0;dark astra 0;aquila 0;bellator 0;ceslsus 0`", color=self.color))
            return
        parameters = parameters.lower().split(';')

        for what in parameters:
            if what == "": continue
            found = False
            for t in types:
                if what.startswith(t):
                    found = True
                    id = types[t]
                    what = what[len(t):]
                    if what == "":
                        await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Please add the step (example: ssr3, sr2, oracle4)", color=self.color))
                        return
                    if what in sumsteps:
                        if str(ctx.author.id) not in self.bot.arca:
                            self.bot.arca[str(ctx.author.id)] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                        self.bot.arca[str(ctx.author.id)][id] = sumsteps[what]
                        self.bot.savePending = True
                        await ctx.message.add_reaction('✅') # white check mark
                    else:
                        await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I can't parse this value: `" + what + "`", color=self.color))
                    break
            if found: continue
            items = {"sephira ":10, "sephira stone ":10, "sephira stones ":10, "fire astra ":11, "water astra ":12, "earth astra ":13, "dirt astra ":13, "wind astra ":14, "light astra ":15, "dark astra ":16, "aquila fragment":17, "aquila":17, "bellator fragment":18, "bellator":18, "celsus fragment":19, "celsus":19}
            for i in items:
                if what.startswith(i):
                    found = True
                    id = items[i]
                    what = what[len(i):]
                    try:
                        v = int(what)
                        if v < 0: raise Exception()
                    except:
                        await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I can't parse this value: `" + what + "`, not a positive number", color=self.color))
                        return
                    if str(ctx.author.id) not in self.bot.arca:
                        self.bot.arca[str(ctx.author.id)] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    self.bot.arca[str(ctx.author.id)][id] = v
                    self.bot.savePending = True
                    await ctx.message.add_reaction('✅') # white check mark
                    break
            if found: continue
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Unknown parameter `" + what + "`\nUse `help aSet` for details.", color=self.color))
            return

    def arcaStepToString(self, step):
        if step == 0: return "None"
        elif step == 1: return "{} ☆☆☆".format(self.bot.getEmote('SR'))
        elif step == 2: return "{} ★☆☆".format(self.bot.getEmote('SR'))
        elif step == 3: return "{} ★★☆".format(self.bot.getEmote('SR'))
        elif step == 4: return "{} ★★★".format(self.bot.getEmote('SR'))
        elif step == 5: return "{} ★★★☆☆".format(self.bot.getEmote('SSR'))
        elif step == 6: return "{} ★★★★☆".format(self.bot.getEmote('SSR'))
        elif step == 7: return "{} ★★★★★".format(self.bot.getEmote('SSR'))
        elif step == 8: return "{} ☆☆☆☆".format(self.bot.getEmote('question'))
        elif step == 9: return "{} ★☆☆☆".format(self.bot.getEmote('question'))
        elif step == 10: return "{} ★★☆☆".format(self.bot.getEmote('question'))
        elif step == 11: return "{} ★★★☆".format(self.bot.getEmote('question'))
        elif step == 12: return "{} ★★★★".format(self.bot.getEmote('question'))
        raise Exception("Invalid Arcarum Step Value")

    def arcaStepToItem(self, step, item):
        table = [
            [0, 0, 0],
            [2, 3, 0],
            [7, 8, 0],
            [17, 18, 0],
            [32, 33, 0],
            [62, 63, 0],
            [107, 108, 10],
            [107, 108, 30],
            [137, 308, 30],
            [137, 308, 30],
            [137, 309, 30],
            [137, 311, 30],
            [137, 314, 30]
        ]
        return table[step][item]

    def arcaDataToItem(self, data, item):
        v = 0
        for i in range(0, 10):
            v += self.arcaStepToItem(data[i], item)
        return v

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['arcasee'])
    @isAuthorized()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def aSee(self, ctx, member : discord.Member = None):
        """See the arcarum progress of a member"""
        if member is None: member = ctx.author
        id = str(member.id)
        if id not in self.bot.arca:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description=member.display_name + " didn't set its progress yet", color=self.color))
        else:
            try:
                msg1 = "**Justice** ▪ {}\n**Hanged Man** ▪ {}\n**Death** ▪ {}\n**Temperance** ▪ {}\n**Devil** ▪ {}\n**Tower** ▪ {}\n**Star** ▪ {}\n**Moon** ▪ {}\n**Sun** ▪ {}\n**Judgement** ▪ {}\n".format(self.arcaStepToString(self.bot.arca[id][0]), self.arcaStepToString(self.bot.arca[id][1]), self.arcaStepToString(self.bot.arca[id][2]), self.arcaStepToString(self.bot.arca[id][3]), self.arcaStepToString(self.bot.arca[id][4]), self.arcaStepToString(self.bot.arca[id][5]), self.arcaStepToString(self.bot.arca[id][6]), self.arcaStepToString(self.bot.arca[id][7]), self.arcaStepToString(self.bot.arca[id][8]), self.arcaStepToString(self.bot.arca[id][9]))

                item_show = [
                    ["Sephira Stones", 1370, self.bot.arca[id][10] + self.arcaDataToItem(self.bot.arca[id], 0)],
                    ["Fire Astras", 628, self.bot.arca[id][11] + self.arcaStepToItem(self.bot.arca[id][4], 1) + self.arcaStepToItem(self.bot.arca[id][8], 1)],
                    ["Water Astras", 628, self.bot.arca[id][12] + self.arcaStepToItem(self.bot.arca[id][0], 1) + self.arcaStepToItem(self.bot.arca[id][7], 1)],
                    ["Earth Astras", 628, self.bot.arca[id][13] + self.arcaStepToItem(self.bot.arca[id][1], 1) + self.arcaStepToItem(self.bot.arca[id][5], 1)],
                    ["Wind Astras", 628, self.bot.arca[id][14] + self.arcaStepToItem(self.bot.arca[id][3], 1) + self.arcaStepToItem(self.bot.arca[id][9], 1)],
                    ["Light Astras", 314, self.bot.arca[id][15] + self.arcaStepToItem(self.bot.arca[id][6], 1)],
                    ["Dark Astras", 314, self.bot.arca[id][16] + self.arcaStepToItem(self.bot.arca[id][2], 1)],
                    ["Aquila Fragment", 90, self.bot.arca[id][17] + self.arcaStepToItem(self.bot.arca[id][1], 2) + self.arcaStepToItem(self.bot.arca[id][4], 2) + self.arcaStepToItem(self.bot.arca[id][8], 2)],
                    ["Bellator Fragment", 90, self.bot.arca[id][18] + self.arcaStepToItem(self.bot.arca[id][0], 2) + self.arcaStepToItem(self.bot.arca[id][7], 2) + self.arcaStepToItem(self.bot.arca[id][9], 2)],
                    ["Celsus Fragment", 120, self.bot.arca[id][19] + self.arcaStepToItem(self.bot.arca[id][2], 2) + self.arcaStepToItem(self.bot.arca[id][3], 2) + self.arcaStepToItem(self.bot.arca[id][5], 2) + self.arcaStepToItem(self.bot.arca[id][6], 2)]
                ]
                mean = 0.0
                msg2 = ""
                for idt in item_show:
                    v = min(idt[1], idt[2])
                    mean += v / (idt[1] * 1.0)
                    msg2 += "**{}** ▪ {} / {} ({:.2f}%)\n".format(idt[0], v, idt[1], 100.0 * v / (idt[1] * 1.0))

                mean = 100 * mean / (len(item_show)*1.0)
                msg2 = "**Total Progression** ▪ {:.2f}%\n".format(mean) + msg2

                await ctx.send(embed=self.bot.buildEmbed(title="**Arcarum Progress of {}**".format(member.display_name), fields=[{'name':"{} **Summons**".format(self.bot.getEmote('summon')), 'value':msg1}, {'name':"{} **Items**".format(self.bot.getEmote('gold')), 'value':msg2}], inline=True, color=self.color))

            except Exception as e:
                await self.bot.sendError('arcasee', str(e))
                return

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['lucihl', 'buncle'])
    async def lucilius(self, ctx, page : int = 0):
        """Lucilius HL Guide - Buncle guide"""
        if ctx.author.id != self.bot.ids['owner']: return
        if page < 1 or page > 8:
            description = "Please use this command with the section number:\n**#1** ▫️ What you need?\n**#2** ▫️ What the group needs?\n**#3** ▫️ Before Starting\n**#4** ▫️ Phase 1 ▫️ Dark Wings 100% - 50%\n**#5** ▫️ Phase 2 ▫️ Dark Wings 50% (Labors)\n**#6** ▫️ Phase 2 ▫️ Dark Wings 50% - 0%\n**#7** ▫️ Phase 3 ▫️ Lucilius 100% - 25%\n**#8** ▫️ Phase 4 ▫️ Lucilius 25% - 0%"
        elif page == 1:
            description = "**What you need?**\n\n▫️ 30,000 {}\n▫️ 2 or 3 carbuncles of your weak element (fire if you are wind) or same element (for dark and light)\n▫️ 2 or 3 dispels (the more the better)\n▫️ If possible: Substitute {} (Spartan gets a 50% cut from it)\n▫️ If possible: Delays {}\n▫️ If possible: A way of surviving a Skyfall-like ougi\n▫️ No characters of the same race (**even on the backline**)".format(self.bot.getEmote('hp'), self.bot.getEmote('sub'), self.bot.getEmote('delay'))
        elif page == 2:
            description = "**What the group needs?**\n\n▫️ A player with Yurius {}\n▫️ A player with Gravity {} (usually the wind player)\n▫️ A player capable of Overchain **(OC)** {}\n▫️ A player capable of tanking Paradise Lost **(PL)**\n▫️ A player capable of 30 hits in one turn\n▫️ A way of having 10 debuffs on the foes\n▫️ **NO** plain damage above two millions\n▫️ A few clarities {}\nAs you improve, some of those can be ignored.".format(self.bot.getEmote('yurius'), self.bot.getEmote('gravity'), self.bot.getEmote('overchain'), self.bot.getEmote('clarity'))
        elif page == 3:
            description = "**Before Starting**\n\n▫️ If **both** foes have their charge diamonds maxed, Lucilius will cast **Paradise Lost**.\nYou need full cut, unchallenged or high defense to survive it, so use your delay properly.\nAfter 50%, during the normal mode, he doesn't cast **PL**.\n▫️ The Blade {} stack increases after each special attack.\nIt increases the foe attack and does annoying things to you (dispel, debuff).\n**Dispel** it as much as possible.".format(self.bot.getEmote('blade'))
        elif page == 4:
            description = "**Phase 1 ▫️ Dark Wings 100% - 50%**\n\n▫️ You get hit by 30,000 damages right when joining, heal back and dispel\n▫️ Gravity {} should be casted on Lucilius.\n▫️ Don't move without phalanx unless you know what you are doing.\n▫️ Normal mode ougi is Phosphorus: High single target damage and dispel. Use a mirror image or substitute to get 100% cut.\n▫️ Overdrive mode ougi is Iblis: Not dangerous but cast annoying debuffs on the party. Save your clears and veils for those.\n▫️ Dark wings alternate between two ougis: The first one removes the damage cap on Lucilius and inflicts Forbidden Fruit on you (if you ougi, you take 10,000 plain damage), the second puts back the damage cap and inflicts Fruit of Life on you (heal when pressing skills), with Zombie below 50%.\n▫️ At 70%, the Dark Wings dispel all debuffs, the Yurius player must reapply them (Gravity is surely still in cooldown so don't bother).\n▫️ The **Countdown starts now** {}. If a player loses a character, it decreases. At 0, the raid is over. DoT and Suicide don't decrease the **CD**.\n▫️ The **OC** player should prepare a 5-man burst before 50%.\n▫️ The **PL** player should try to get full diamonds on both foes beforehand (optional but it helps).\n▫️ Only one player must pass 50%, or the ones following him might just die.".format(self.bot.getEmote('gravity'), self.bot.getEmote('the end'))
        elif page == 5:
            description = "**Phase 2 ▫️ Dark Wings 50% (Labors)**\n\nThe Twelve Labors {} are now up and they each have a different effect on the raid. The goal is to clear the annoying ones and ignore the others.\nHere, you'll find a quick overview of each one.\n▫️ Labor 1 to 6 increases his elemental damage. The corresponding element must do 10,000,000 damage in one turn to clear it. Optional.\n▫️ Labor 7 causes the damage element to be fixed to your weak element. That's what allow us to abuse carbuncles for 100% cut. It's cleared by doing 2,000,000 plain damage in one turn, so **don't do it**.\n▫️ Labor 8 is the **First one to be cleared**, it nullifies Phalanx. The **OC** player just need to overchain (Phalanx will work after, so be sure to phalanx him).\n▫️ Labor 9 heals Lucilius every turn. You need to inflict 30 hits in one turn to remove it. Kill the wings first if you can't guarantee it.\n▫️ Labor 10 puts debuffs on your party. You need 10 debuffs at the end of the turn to clear it. This one is skippable but it can be nice to clear it.\n▫️ Labor 11 **dispels two buffs** on your party every turn. It makes this phase very dangerous until the overdrive, because the **PL** player must do his job here, and **PL** doesn't happen until the overdrive now.\n▫️ Labor 12 inflicts plain damage every turns and you gotta clear all labors to remove it. But we don't in buncle runs (**Labor 7 must not be removed**).".format(self.bot.getEmote('labor'))
        elif page == 6:
            description = "**Phase 2 ▫️ Dark Wings 50% - 0%**\n\n▫️ First, debuffs (don't gravity unless the **PL** player is ok with it) and phalanx. The **OC** player must now Overchain to remove Labor **8**.\n▫️ You can use carbuncles now but Labor **11** will remove your last two buffs. Use a buncle before receiving phalanx is a good trick.\n▫️ Clear Labor **10** if you can.\n▫️ Push him to Overdrive as soon as possible (Dark Wings and Lucilius share the same mode bar) so the **PL** player can clear Labor **11**. If he hasn't aligned the diamonds beforehand, he must do it as soon as possible.\n▫️ Once done, you can breath and relax. Clear Labor **9** whenever you can and focus on killing the Dark Wings.\n▫️ Don't forget to dispel the Blade {} stack. It goes up way faster when Labor **11** is up.\n▫️ Care for Lucilius' HP. At 95%, he casts Phosphorus.".format(self.bot.getEmote('blade'))
        elif page == 7:
            description = "**Phase 3 ▫️ Lucilius 100% - 25%**\n\nIf you are all alive at this point, it should be now fairly easy:\n▫️ 95%: Phosphorus, use Substitute {} with Phalanx, or a Carbuncle with Phalanx, or Mirror image.\n▫️ 85%: Axion, 3-hits damage. Same strategy as Phosphorus. Don't die to this because, if you do, he will then inflicts 30,000 plain damage.\n▫️ 70%: Diamonds fill. Don't waste your delay {} just before.\n▫️ 60%: Axion again but to all ally. **Substitute doesn't work here**.\n▫️ 55%: Diamonds fill, again.\nNever forget to dispel him.\nThose triggers expire after a certain point.\nUse your summons, if needed, before 25%.".format(self.bot.getEmote('sub'), self.bot.getEmote('delay'))
        elif page == 8:
            description = "**Phase 4 ▫️ Lucilius 25% - 0%**\n\nLucilius dispels all debuffs at 25% and 10%. He now has Heaven's Floodgates, a Turn up field effect similar to Akasha HL's.\nYou are also inflicted with summonless, now.\n\n▫️ 25%: Gopherwood Ark, the Race check. If you have two or more characters sharing the same race, the 2nd and more will die, **even on the backline**. Don't pass this trigger if you'll lose an important character or cause the **CD** {} to reaches 0.\n▫️ 20% & 15%: Axion Apocalypse 3-hits damage, increase the Blade {} stack by 1. You can use Substitute {}.\n▫️ 10% & 3%: Paradise Lost (Special). 999,999 damage. You need full cut or unchallenged to pass this. If you use Dark Zooey's Conjunction, uses a blue pot because Labor **12** now does 5,000 plain damage. All-ally substitute (Light Vira for example) and Centurion II lets you tank those trigger without damage (it doesn't work that way, normally).".format(self.bot.getEmote('countdown'), self.bot.getEmote('blade'), self.bot.getEmote('sub'))

        try:
            await ctx.author.send(embed=self.bot.buildEmbed(title="{} Dark Rapture (Hard) ▫️ Buncle Guide".format(self.bot.getEmote('lucilius')), description=description, footer="version 1.0", color=self.color))
            await ctx.message.add_reaction('✅') # white check mark
        except:
            await ctx.author.send(embed=self.bot.buildEmbed(title="Error", description="I can't send you a direct message", color=self.color))