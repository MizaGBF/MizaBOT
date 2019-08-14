import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random

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
                msg = self.bot.getEmoteStr('cog') + " Maintenance in **" + str(d.days) + "d" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**, for **" + str(self.bot.maintenance['duration']) + " hour(s)**"
            else:
                d = current_time - self.bot.maintenance['time']
                if self.bot.maintenance['duration'] <= 0:
                    msg = self.bot.getEmoteStr('cog') + " Emergency maintenance on going"
                elif (d.seconds // 3600) >= self.bot.maintenance['duration']:
                    self.bot.maintenance = {"state" : False, "time" : None, "duration" : 0}
                    self.bot.savePending = True
                else:
                    e = self.bot.maintenance['time'] + timedelta(seconds=3600*self.bot.maintenance['duration'])
                    d = e - current_time
                    msg = self.bot.getEmoteStr('cog') + " Maintenance ends in **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**"
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
                if full: await ctx.send("Click here :point_right: " + url)
                else: await ctx.send(embed=self.bot.buildEmbed(title=" ".join(terms) + " search result", description="Click here :point_right: " + url, color=self.color))
            except Exception as e:
                if str(e) != "HTTP Error 404: Not Found":
                    await self.bot.sendError("wiki", str(e))
                await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Click here to refine the search\nhttps://gbf.wiki/index.php?title=Special:Search&search=" + " ".join(terms), color=self.color, footer=str(e)))


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
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="`" + term + "` isn't in my database", footer="Use the help for the full list", color=self.color))
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

        title = self.bot.getEmoteStr('clock') + " Current Time: " + str(current_time.hour).zfill(2) + ":" + str(current_time.minute).zfill(2)

        reset = current_time.replace(hour=5, minute=0, second=0, microsecond=0)
        if current_time.hour >= reset.hour:
            reset += timedelta(days=1)
        d = reset - current_time
        description = self.bot.getEmoteStr('mark') + " Reset in **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**"

        id = str(ctx.message.author.guild.id)
        if id in self.bot.st:
            st1 = current_time.replace(hour=self.bot.st[id][0], minute=0, second=0, microsecond=0)
            st2 = st1.replace(hour=self.bot.st[id][1])

            if current_time.hour >= st1.hour:
                st1 += timedelta(days=1)
            if current_time.hour >= st2.hour:
                st2 += timedelta(days=1)

            d = st1 - current_time
            if d.seconds >= 82800: description += "\n" + self.bot.getEmoteStr('st') + " Strike times in " + self.bot.getEmoteStr('1') + " **NOW!** "
            else: description += "\n" + self.bot.getEmoteStr('st') + " Strike times in " + self.bot.getEmoteStr('1') + " **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m** "
            d = st2 - current_time
            if d.seconds >= 82800: description += self.bot.getEmoteStr('2') + " **right now!**"
            else: description += self.bot.getEmoteStr('2') + " **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**"

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
                await ctx.send(embed=self.bot.buildEmbed(title="Last Gacha update", description=str(l) + " new ticket(s)", thumbnail=tickets[-1], color=self.color))
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

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isYou()
    async def lucilius(self, ctx):
        """Post the (You) lucilius spreadsheet
        (You) server only"""
        if ctx.message.author.guild.id == self.bot.ids['you_server']:
            await ctx.send(embed=self.bot.buildEmbed(title="(You) Lucilius Sheet", description=self.bot.strings["lucilius()"], thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/592019627677188116/BattleRaid_Lucilius_ImpossibleHard.png", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I'm not permitted to post this link here", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['arcarum', 'arca', 'oracle', 'evoker', 'astra'])
    async def arcanum(self, ctx):
        """Post a link to my autistic Arcanum Sheet"""
        await ctx.send(embed=self.bot.buildEmbed(title="Arcanum Tracking Sheet", description=self.bot.strings["arcanum()"], thumbnail="http://game-a.granbluefantasy.jp/assets_en/img_low/sp/assets/item/article/s/250" + str(random.randint(1, 46)).zfill(2) + ".jpg", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['sparktracker'])
    async def rollTracker(self, ctx):
        """Post a link to my autistic roll tracking Sheet"""
        await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('crystal') + " GBF Roll Tracker", description=self.bot.strings["rolltracker()"], color=self.color))

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

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    async def leak(self, ctx):
        """Post a link to the /gbfg/ leak pastebin"""
        await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ Leak Pastebin", description=self.bot.strings["leak()"], color=self.color))

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
                    cd = str(d.days) + "d" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m"
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
                    msg += self.bot.schedule[i] + ";" + self.bot.schedule[i+1]
                elif l > 12: # enable or not emotes (I have 6 numbered emotes, so 6 field max aka 12 elements in my array)
                    msg += self.bot.schedule[i] + " ▪ " + self.bot.schedule[i+1] + "\n"
                else:
                    msg += self.bot.getEmoteStr(str((i//2)+1)) + " " + self.bot.schedule[i] + " ▪ " + self.bot.schedule[i+1] + "\n"
                i += 2
            if raw == 'raw': msg += "`"
            await ctx.send(embed=self.bot.buildEmbed(title="🗓 Event Schedule " + self.bot.getEmoteStr('clock') + " {0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST()), url="https://twitter.com/granblue_en", color=self.color, description=msg))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tokens', 'box'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def token(self, ctx, box : int):
        """Calculate how many tokens you need"""
        if box < 0: box = 0
        t = box * 2000
        if box > 44:
            t = (t - 88000) * 3 + 88000
        await ctx.send(embed=self.bot.buildEmbed(title="Token Calculator", description="You need **{:,}** token(s) for **".format(t) + str(box) + "** box(s)", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gbfvs', 'versus'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def gbfv(self, ctx):
        """Post the time to the next Versus beta"""
        return
        c = self.bot.getJST()
        betas = [
            [c.replace(year=2019, month=5, day=31, hour=18, minute=0, second=0, microsecond=0), c.replace(year=2019, month=5, day=31, hour=23, minute=0, second=0, microsecond=0)],
            [c.replace(year=2019, month=6, day=1, hour=10, minute=0, second=0, microsecond=0), c.replace(year=2019, month=6, day=1, hour=15, minute=0, second=0, microsecond=0)],
            [c.replace(year=2019, month=6, day=2, hour=1, minute=0, second=0, microsecond=0), c.replace(year=2019, month=6, day=2, hour=6, minute=0, second=0, microsecond=0)]
        ]
        msg = ""
        for i in range(0, len(betas)):
            if c < betas[i][0]:
                delta = betas[i][0] - c
                msg += "Test period " + self.bot.getEmoteStr(str(i+1)) + " starts in **" + str(delta.days) + "d" + str(delta.seconds // 3600) + "h" + str((delta.seconds // 60) % 60) + "m**\n"
            elif c < betas[i][1]:
                delta = betas[i][1] - c
                msg += "Test period " + self.bot.getEmoteStr(str(i+1)) + " is **on going** and ends in **" + str(delta.days) + "d" + str(delta.seconds // 3600) + "h" + str((delta.seconds // 60) % 60) + "m**\n"
            else:
                msg += "Test period " + self.bot.getEmoteStr(str(i+1)) + " is over\n"
        await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('clock') + " GBF Versus ▪ Beta Calendar", description=msg, url="https://versus.granbluefantasy.jp/en/closedbeta/", thumbnail="https://versus.granbluefantasy.jp/en/assets/images/footer_cyg.png", color=self.color))

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
                        await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('clock') + " Premium Friday", description="Premium Friday ends in **" + str(end.days) + "d" + str(end.seconds // 3600) + "h" + str((end.seconds // 60) % 60) + "m**", url="http://game.granbluefantasy.jp", thumbnail=thumbnail, color=self.color))
                        return
                    elif c >= end:
                        pass
                    elif c < beg:
                        last = beg
                        searching = False
                else:
                    searching = False
        last = last.replace(hour=15, minute=00, second=00) - c
        await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('clock') + " Premium Friday", description="Premium Friday starts in **" + str(last.days) + "d" + str(last.seconds // 3600) + "h" + str((last.seconds // 60) % 60) + "m**",  url="http://game.granbluefantasy.jp", thumbnail=thumbnail, color=self.color))

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
        await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('clock') + " Kore Kara", description="Release approximately in **" + str(delta.days) + "d" + str(delta.seconds // 3600) + "h" + str((delta.seconds // 60) % 60) + "m**",  url="https://granbluefantasy.jp/news/index.php", thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png", color=self.color))

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
                if level >= 15: raise Exception("Can't skill up a " + self.bot.getEmoteStr('SR') + " weapon **SL" + str(level) + "**")
                if level >= 5:
                    msg = "**" + str(level) + "** " + self.bot.getEmoteStr('SR') + " to reach **SL" + str(level+1) + "**"
                else:
                    msg = "**" + str(level) + "** " + self.bot.getEmoteStr('SR') + " or **" + str(level*4) + "** " + self.bot.getEmoteStr('R') + " to reach SL" + str(level+1) + "**"
            elif type in ["ssr", "magna", "omega"]:
                if level >= 20: raise Exception("Can't skill up a " + self.bot.getEmoteStr('SSR') + " weapon **SL" + str(level) + "**")
                if level >= 15: 
                    msg = "**" + str(level) + "** " + self.bot.getEmoteStr('SSR') + " to reach **SL" + str(level+1) + "**"
                elif level > 10: 
                    msg = "**2** " + self.bot.getEmoteStr('SSR') + " and **" + str((level-10)*2) + "** " + self.bot.getEmoteStr('SR') + " to reach **SL" + str(level+1) + "**"
                elif level == 10: 
                    msg = "**2** " + self.bot.getEmoteStr('SSR') + " to reach **SL" + str(level+1) + "**"
                elif level > 5: 
                    msg = "**1** " + self.bot.getEmoteStr('SSR') + " and **" + str((level-5)*2) + "** " + self.bot.getEmoteStr('SR') + " to reach **SL" + str(level+1) + "**"
                elif level == 5: 
                    msg = "**1** " + self.bot.getEmoteStr('SSR') + " to reach **SL" + str(level+1) + "**"
                else:
                    msg = "**" + str(2*level) + "** " + self.bot.getEmoteStr('SR') + " to reach **SL" + str(level+1) + "**"
            elif type in ["bahamut", "baha", "ultima", "seraph", "seraphic", "opus"]:
                if level >= 20: raise Exception("Can't skill up a " + self.bot.getEmoteStr('SSR') + " weapon **SL" + str(level) + "**")
                if level == 19: 
                    msg = "**32** " + self.bot.getEmoteStr('SSR') + " or **8** " + self.bot.getEmoteStr('SSR') + " SL4 to reach **SL" + str(level+1) + "**"
                elif level == 18: 
                    msg = "**30** " + self.bot.getEmoteStr('SSR') + " or **6** " + self.bot.getEmoteStr('SSR') + " SL4 and **2** " + self.bot.getEmoteStr('SSR') + " SL3 to reach **SL" + str(level+1) + "**"
                elif level == 17: 
                    msg = "**29** " + self.bot.getEmoteStr('SSR') + " or **5** " + self.bot.getEmoteStr('SSR') + " SL4 and **3** " + self.bot.getEmoteStr('SSR') + " SL3 to reach **SL" + str(level+1) + "**"
                elif level == 16: 
                    msg = "**27** " + self.bot.getEmoteStr('SSR') + " or **6** " + self.bot.getEmoteStr('SSR') + " SL4 and **1** " + self.bot.getEmoteStr('SSR') + " SL3 to reach **SL" + str(level+1) + "**"
                elif level == 15: 
                    msg = "**25** " + self.bot.getEmoteStr('SSR') + " or **4** " + self.bot.getEmoteStr('SSR') + " SL4 and **3** " + self.bot.getEmoteStr('SSR') + " SL3 to reach **SL" + str(level+1) + "**"
                else:
                    msg = "**" + str(level) + "** " + self.bot.getEmoteStr('SSR') + " to reach **SL" + str(level+1) + "**"
            else:
                raise Exception("Unknown type `" + type + "`")
            await ctx.send(embed=self.bot.buildEmbed(title="Skill Level Calculator", description=msg,  url="https://gbf.wiki/Raising_Weapon_Skills", color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Skill Level Calculator", description=str(e),  url="https://gbf.wiki/Raising_Weapon_Skills", color=self.color))
