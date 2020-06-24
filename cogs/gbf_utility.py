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
        self.rankre = re.compile("Rank ([0-9])+")
        self.sumre = re.compile("<div id=\"js-fix-summon([0-9]{2})-name\" class=\"prt-fix-name\" name=\"[A-Za-z'-. ]+\">(Lvl [0-9]+ [A-Za-z'-. ]+)<\/div>")
        self.starre = re.compile("<span class=\"prt-current-npc-name\">\s*(Lvl [0-9]+ [A-Za-z'-.μ ]+)\s*<\/span>")
        self.starcomre = re.compile("<div class=\"prt-pushed-info\">(.+)<\/div>")
        self.empre = re.compile("<div class=\"txt-npc-rank\">([0-9]+)<\/div>")
        self.starringre = re.compile("<div class=\"ico-augment2-s\"><\/div>\s*<\/div>\s*<div class=\"prt-pushed-spec\">\s*<div class=\"prt-pushed-info\">")
        self.starplusre = re.compile("<div class=\"prt-quality\">(\+[0-9]+)<\/div>")
        self.badprofilecache = []
        self.badcrewcache = []
        self.crewcache = {}
        self.possiblesum = {'10':'fire', '20':'water', '30':'earth', '40':'wind', '50':'light', '60':'dark', '00':'misc', '01':'misc'}
        self.subsum = {'chev':'luminiera omega', 'chevalier':'luminiera omega', 'lumi':'luminiera omega', 'luminiera':'luminiera omega', 'colossus':'colossus omega', 'colo':'colossus omega', 'leviathan':'leviathan omega', 'levi':'leviathan omega', 'yggdrasil':'yggdrasil omega', 'yugu':'yggdrasil omega', 'tiamat':'tiamat omega', 'tia':'tiamat omega', 'celeste':'celeste omega', 'boat':'celeste omega', 'alex':'godsworn alexiel', 'alexiel':'godsworn alexiel', 'zeph':'zephyrus', 'longdong':'huanglong', 'dong':'huanglong', 'long':'huanglong', 'bunny':'white rabbit', 'kirin':'qilin', 'sylph gacha':'sylph, flutterspirit of purity', 'poseidon gacha':'poseidon, the tide father', 'anat gacha':'anat, for love and war', 'cerberus gacha':'cerberus, hellhound trifecta', 'marduck gacha':'marduk, battlefield reaper'}
        self.conn = None
        self.cursor = None
        self.sqllock = False

    def startTasks(self):
        self.bot.runTask('summon', self.summontask)

    async def isGBFAvailable(self):
        current_time = self.bot.getJST()
        req = None
        if self.bot.maintenance['state'] and current_time < self.bot.maintenance['time']: # before maintenance
            req = await self.requestGBF()
            if self.bot.getJST() >= self.bot.maintenance['time']:
                return False
        elif self.bot.maintenance['state'] and current_time >= self.bot.maintenance['time'] and (self.bot.maintenance['duration'] == 0 or current_time < self.bot.maintenance['time'] + timedelta(seconds=self.bot.maintenance['duration']*3600+30)): # during maintenance
            return False
        elif self.bot.maintenance['state'] and current_time > self.bot.maintenance['time'] + timedelta(seconds=self.bot.maintenance['duration']*3600+30): # after maintenance
            req = await self.requestGBF()
            self.bot.maintenance = {"state" : False, "time" : None, "duration" : 0}
            self.bot.savePending = True
        else:
            req = await self.requestGBF()

        if req is not None and req[0].status == 200 and req[1].find("The app is now undergoing") != -1:
            await self.bot.send('debug', embed=self.bot.buildEmbed(title="Emergency maintenance detected", timestamp=datetime.utcnow(), color=self.color))
            self.bot.maintenance['time'] = current_time
            self.bot.maintenance['duration'] = 0
            self.bot.maintenance['state'] = True
            self.bot.savePending = True
            return False
            
        return True

    async def summontask(self): # summon update task
        while True:
            try:
                uptime = self.bot.uptime(False)
                if self.bot.summonlast is None: delta = None
                else: delta = self.bot.getJST() - self.bot.summonlast
                if uptime.seconds > 3600 and uptime.seconds < 30000 and (delta is None or delta.days >= 5):
                    await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="summontask()", description="auto update started", timestamp=datetime.utcnow()))
                    await self.updateSummon()
                    await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="summontask()", description="auto update ended", timestamp=datetime.utcnow()))
                    await asyncio.sleep(80000)
                    return
                else:
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                await self.bot.sendError('summontask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('summontask', str(e))

    async def loadSumDB(self):
        try:
            if self.sqllock:
                self.conn = None
            elif self.bot.drive.dlFile("summon.sql", self.bot.tokens['files']):
                self.conn = sqlite3.connect("summon.sql")
                self.cursor = self.conn.cursor()
            else:
                self.conn = None
        except Exception as e:
            self.conn = None
            await self.bot.sendError('loadSumDB', str(e))
        return (self.conn is not None)

    async def checkSumDB(self, ctx):
        if self.conn:
            return True
        else:
            await self.bot.react(ctx, 'time')
            r = await self.loadSumDB()
            await self.bot.unreact(ctx, 'time')
            return r

    async def getCrewData(self, ctx, target):
        cog = self.bot.get_cog('Baguette') # secret sauce to access the game
        if cog is None: {'error':''}

        if not await self.isGBFAvailable(): # check for maintenance
            return {'error':'Game is in maintenance'}
        id = " ".join(target)
        id = self.bot.granblue['gbfgcrew'].get(id.lower(), id) # check if the id is a gbfgcrew
        # check id validityy
        try:
            id = int(id)
        except:
            if id == "": return {'error':"Please input the id or the name of the crew\nOnly some crews are registered, please input an id instead"}
            return {'error':"Invalid name `{}`\nOnly some crews are registered, please input an id instead".format(id)}
        if id < 0 or id >= 10000000:
            return {'error':'Out of range ID'}
        if id in self.badcrewcache: # if already searched (to limit bad requests)
            return {'error':'Crew not found'}

        crew = {'scores':[], 'id':id}
        if id in self.crewcache: # public crews are stored until next reboot (to limit the request amount)
            crew = self.crewcache[id]
        else:
            for i in range(0, 4): # for each page (page 0 being the crew page, 1 to 3 being the crew page
                get = cog.requestCrew(id, i)
                if get is None:
                    if i == 0: # if error on page 0, the crew doesn't exist
                        self.badcrewcache.append(id)
                        return {'error':'Crew not found'}
                    elif i == 1: # if error on page 1, the crew is private
                        crew['private'] = True
                    break
                else:
                    # store the data
                    if i == 0:
                        crew['timestamp'] = datetime.utcnow()
                        crew['footer'] = ""
                        crew['private'] = False # in preparation
                        crew['name'] = su.unescape(get['guild_name'])
                        crew['rank'] = get['guild_rank']
                        crew['ship'] = "http://game-a.granbluefantasy.jp/assets_en/img/sp/guild/thumb/top/{}.png".format(get['ship_img'])
                        crew['ship_element'] = {"10001":"wind", "20001":"fire", "30001":"water", "40001":"earth"}.get(get['ship_img'].split('_')[0], 'gw')
                        crew['leader'] = su.unescape(get['leader_name'])
                        crew['leader_id'] = get['leader_user_id']
                        crew['donator'] = su.unescape(get['most_donated_name'])
                        crew['donator_id'] = get['most_donated_id']
                        crew['donator_amount'] = get['most_donated_lupi']
                        crew['message'] = su.unescape(get['introduction'])
                        crew['total_rank'] = 0
                    else:
                        if 'player' not in crew: crew['player'] = []
                        for p in get['list']:
                            crew['total_rank'] += int(p['level'])
                            crew['player'].append({'id':p['id'], 'name':su.unescape(p['name']), 'level':p['level'], 'is_leader':p['is_leader'], 'member_position':p['member_position'], 'honor':None}) # honor is a placeholder

            # prepare the member list
            fields = []
            if not crew['private']:
                crew['average'] = round(crew['total_rank'] / (len(crew['player']) * 1.0))
            if not crew['private']: self.crewcache[id] = crew # only cache public crews

        # get the last gw score
        cog = self.bot.get_cog('GW')
        if cog is not None:
            crew['scores'] = []
            data = await cog.searchGWDBCrew(ctx, id, 2)
            if data is not None:
                for n in range(0, 2):
                    if data[n] is not None and 'result' in data[n] and len(data[n]['result']) == 1:
                        possible = {11:"Total Day 4", 9:"Total Day 3", 7:"Total Day 2", 5:"Total Day 1", 3:"Total Prelim."}
                        for ps in possible:
                            if data[n]['result'][0][ps] is not None:
                                if ps == 11 and data[n]['result'][0][0] is not None:
                                    crew['scores'].append("{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors ".format(self.bot.getEmote('gw'), data[n].get('gw', ''), data[n]['result'][0][0], data[n]['result'][0][ps]))
                                    break
                                else:
                                    crew['scores'].append("{} GW**{}** ▫️ {} ▫️ **{:,}** honors ".format(self.bot.getEmote('gw'), data[n].get('gw', ''), possible[ps], data[n]['result'][0][ps]))
                                    break

        return crew

    def honorFormat(self, h): # convert honor number to a shorter string version
        if h is None: return "n/a"
        elif h >= 1000000000: return "{:.1f}B".format(h/1000000000)
        elif h >= 1000000: return "{:.1f}M".format(h/1000000)
        elif h >= 1000: return "{:.1f}K".format(h/1000)
        return h

    async def postCrewData(self, ctx, id, mode = 0): # mode 0 = auto, 1 = gw mode disabled, 2 = gw mode enabled
        cog = self.bot.get_cog('GW')
        if cog is None: mode = 1 # requires GW cog
        try:
            # retrieve formatted crew data
            crew = await self.getCrewData(ctx, id)

            if 'error' in crew: # print the error if any
                if len(crew['error']) > 0:
                    await ctx.send(embed=self.bot.buildEmbed(title="Crew Error", description=crew['error'], color=self.color))
                return

            # embed initialization
            title = "\u202d{} **{}**".format(self.bot.getEmote(crew['ship_element']), crew['name'])
            description = "💬 ``{}``".format(self.escape(crew['message']))
            footer = ""
            fields = []

            # append GW scores if any
            for s in crew['scores']:
                description += "\n{}".format(s)

            if crew['private']:
                description += '\n{} [{}](http://game.granbluefantasy.jp/#profile/{}) ▫️ *Crew is private*'.format(self.bot.getEmote('captain'), crew['leader'], crew['leader_id'])
            else:
                # set title and footer
                title += " ▫️ {}/30 ▫️ Rank {}".format(len(crew['player']), crew['average'])
                footer = "Public crews are updated once per day"
                # get GW data
                if mode == 2: gwstate = True
                elif mode == 1: gwstate = False
                else: gwstate = cog.isGWRunning()
                players = crew['player'].copy()
                gwid = None
                if gwstate:
                    total = 0
                    unranked = 0
                    for i in range(0, len(players)):
                        # retrieve player honors
                        honor = await cog.searchGWDBPlayer(ctx, players[i]['id'], 2)
                        if honor[1] is None or len(honor[1]) == 0 or len(honor[1]['result']) == 0:
                            players[i]['honor'] = None
                            unranked += 1
                        else:
                            res = honor[1].get('result', [None, None, None, None])
                            if gwid is None: gwid = honor[1].get('gw', None)
                            if res is not None and len(res[0]) != 0 and res[0][3] is not None:
                                players[i]['honor'] = res[0][3]
                                total += res[0][3]
                            else:
                                players[i]['honor'] = None
                                unranked += 1
                        if i > 0 and players[i]['honor'] is not None:
                            # sorting
                            for j in range(0, i):
                                if players[j]['honor'] is None or players[i]['honor'] > players[j]['honor']:
                                    tmp = players[j]
                                    players[j] = players[i]
                                    players[i] = tmp
                    if gwid and len(players) - unranked > 0:
                        description += "\n{} GW**{}** ▫️ Player Total **{}** ▫️ Average **{}**".format(self.bot.getEmote('question'), gwid, self.honorFormat(total), self.honorFormat(total // (len(players) - unranked)))
                        if unranked > 0:
                            description += " ▫️ {} Unranked".format(unranked)
                            if unranked > 1: description += "s"
                # create the fields
                i = 0
                for p in players:
                    if i % 10 == 0: fields.append({'name':'Page {}'.format(self.bot.getEmote('{}'.format(len(fields)+1))), 'value':''})
                    i += 1
                    if p['member_position'] == "1": r = "captain"
                    elif p['member_position'] == "2": r = "foace"
                    elif p['member_position'] == "3": r = "atkace"
                    elif p['member_position'] == "4": r = "deface"
                    else: r = "ensign"
                    entry = '{} [{}](http://game.granbluefantasy.jp/#profile/{})'.format(self.bot.getEmote(r), self.escape(p['name']), p['id'])
                    if gwstate:  entry += " \▫️ {}".format(self.honorFormat(p['honor']))
                    else: entry += " \▫️ r**{}**".format(p['level'])
                    entry += "\n"
                    fields[-1]['value'] += entry

            await ctx.send(embed=self.bot.buildEmbed(title=title, description=description, fields=fields, inline=True, url="http://game.granbluefantasy.jp/#guild/detail/{}".format(crew['id']), footer=footer, timestamp=crew['timestamp'], color=self.color))

        except Exception as e:
            await self.bot.sendError("postCrewData", str(e))

    async def updateSummon(self):
        self.bot.drive.delFiles(["summon.sql"], self.bot.tokens['files'])
        cog = self.bot.get_cog('Baguette')
        if cog is None: return
        try: os.remove('summon.sql')
        except: pass
        self.sqllock = True
        conn = sqlite3.connect('summon.sql')
        c = conn.cursor()
        c.execute('CREATE TABLE players (id int, name text)')
        summonnames = []
        for sid in list(self.bot.gbfids.keys()):
            id = self.bot.gbfids[sid]
            data = await cog.getProfileData(id)
            if data is None:
                continue
            soup = BeautifulSoup(data, 'html.parser')
            try: name = soup.find_all("span", class_="txt-other-name")[0].string
            except: name = None
            if name is not None: # private
                try:
                    c.execute("INSERT INTO players VALUES ({},'{}')".format(id, name.replace("'", "''").replace("%", "\%")))
                    summons_res = self.sumre.findall(data)
                    for s in summons_res:
                        sp = s[1].lower().split() # Lvl 000 Name1 Name2 ... NameN
                        sn = " ".join(sp[2:])
                        if sn not in summonnames:
                            summonnames.append(sn)
                            c.execute('CREATE TABLE `{}` (id int, level int)'.format(sn))
                        c.execute("INSERT INTO `{}` VALUES ({},{})".format(sn, id, sp[1]))
                except:
                    pass
            await asyncio.sleep(0.1)
        conn.commit()
        conn.close()
        self.sqllock = False
        if self.bot.drive.saveDiskFile("summon.sql", "application/sql", "summon.sql", self.bot.tokens['files']):
            self.conn = sqlite3.connect("summon.sql")
            self.cursor = self.conn.cursor()
        self.bot.summonlast = self.bot.getJST()
        self.bot.savePending = True

    def isYou(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isYouServer(ctx)
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

    def escape(self, s): # escape markdown string
        # add the RLO character before
        return '\u202d' + s.replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('[', '').replace(']', '').replace('(', '\\(').replace(')', '\\)').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('|', '\\|')

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

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['time', 'st', 'reset', 'gbf'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def granblue(self, ctx):
        """Post various Granblue Fantasy informations"""
        current_time = self.bot.getJST()
        description = "{:} Current Time is **{:02d}:{:02d} JST**".format(self.bot.getEmote('clock'), current_time.hour, current_time.minute)

        try:
            cog = self.bot.get_cog('Baguette')
            v = cog.getCurrentGameversion()
            if v is not None:
                description += "\n{} Version is `{}` (`{}`)".format(self.bot.getEmote('cog'), v, cog.versionToDateStr(v))
        except Exception as e:
            await self.bot.sendError("getgwstate", str(e))

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
            buf = self.maintenanceUpdate()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("maintenanceUpdate", str(e))

        try:
            cog = self.bot.get_cog('Baguette')
            if cog is not None:
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

        await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))

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
            if cog is None: return
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
            if cog is None: return
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

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['badboi', 'branded', 'restricted'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def brand(self, ctx, id : int):
        """Check if a GBF profile is restricted"""
        try:
            cog = self.bot.get_cog('Baguette')
            if cog is None: return
            if id < 0 or id >= 100000000:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
            data = await cog.getScoutData(id)
            if data == "Maintenance":
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Game is in maintenance", color=self.color))
                return
            elif len(data['user']) == 0:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="In game message:\n`{}`".format(data['no_member_msg'].replace("<br>", " ")), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
                return
            try:
                if data['user']["restriction_flag_list"]["event_point_deny_flag"]:
                    status = "Account is restricted"
                else:
                    status = "Account isn't restricted"
            except:
                status = "Account isn't restricted"
            await ctx.send(embed=self.bot.buildEmbed(title="{} {}".format(self.bot.getEmote('gw'), data['user']['nickname']), description=status, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/talk/{}.png".format(data['user']['image']), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))

        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid ID", color=self.color))
            await self.bot.sendError("brand", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['clearid'])
    @isOwner()
    async def clearProfile(self, ctx, gbf_id : int):
        """Unlink a GBF id (Owner only)"""
        for discord_id in self.bot.gbfids:
            if self.bot.gbfids[discord_id] == gbf_id:
                del self.bot.gbfids[discord_id]
                self.bot.savePending = True
                await self.bot.send('debug', 'User `{}` has been removed'.format(discord_id))
                await ctx.message.add_reaction('✅') # white check mark
                return
        if str(discord_id) not in self.bot.gbfids:
            await ctx.send(embed=self.bot.buildEmbed(title="Clear Profile Error", description="ID not found", color=self.color))
            return

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def forceSummonUpdate(self, ctx):
        """Force update the summon list (Owner only)"""
        await self.bot.react(ctx, 'time')
        await self.updateSummon()
        await self.bot.unreact(ctx, 'time')
        await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def profileStat(self, ctx):
        """Linked GBF id statistics (Owner only)"""
        if self.conn is not None: msg = "Database loaded"
        else:
            if self.sqllock: msg = "Database is locked"
            else: msg = "Database isn't loaded"
        await ctx.send(embed=self.bot.buildEmbed(title="{} Summon statistics".format(self.bot.getEmote('summon')), description="**{}** Registered Users\n{}".format(len(self.bot.gbfids), msg), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['unsetid'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def unsetProfile(self, ctx):
        """Unlink your GBF id"""
        if str(ctx.author.id) not in self.bot.gbfids:
            await ctx.send(embed=self.bot.buildEmbed(title="Unset Profile Error", description="You didn't set your GBF profile ID", color=self.color))
            return
        del self.bot.gbfids[str(ctx.author.id)]
        self.bot.savePending = True
        await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setid'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def setProfile(self, ctx, id : int):
        """Link your GBF id to your Discord ID"""
        try:
            cog = self.bot.get_cog('Baguette')
            if cog is None: return
            if id < 0 or id >= 100000000:
                await ctx.send(embed=self.bot.buildEmbed(title="Set Profile Error", description="Invalid ID", color=self.color))
                return
            data = await cog.getProfileData(id)
            if data is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Set Profile Error", description="Profile not found", color=self.color))
                return
            for u in self.bot.gbfids:
                if self.bot.gbfids[u] == id:
                    await ctx.send(embed=self.bot.buildEmbed(title="Set Profile Error", description="This id is already in use", footer="use the bug_report command if it's a case of griefing", color=self.color))
                    return
            # register
            self.bot.gbfids[str(ctx.author.id)] = id
            self.bot.savePending = True
            await ctx.message.add_reaction('✅') # white check mark
        except Exception as e:
            await self.bot.sendError("setprofile", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['friend'])
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def summon(self, ctx, *search : str):
        """Search a summon
        <summon name> or <level min> <summon name>
         or <summon name> <level min>"""
        if not await self.checkSumDB(ctx):
            await ctx.send(embed=self.bot.buildEmbed(title="Summon Error", description="Currently unavailable".format(name), color=self.color))
            return
        try:
            level = int(search[0])
            name = " ".join(search[1:])
        except:
            try:
                level = int(search[-1])
                name = " ".join(search[:-1])
            except:
                level = 0
                name = " ".join(search)
        name = self.subsum.get(name.lower(), name.lower())
        try:
            self.cursor.execute("SELECT * FROM `{}` WHERE level >= {}".format(name.lower(), level))
            data = self.cursor.fetchall()
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Summon Error", description="`{}` ▫️ No one has this summon".format(name), footer="Be sure to type the full name", color=self.color))
            return
        random.shuffle(data)
        msg = ""
        count = 0
        fields = []

        # get thumbnail from the wiki
        try:
            terms = name.split(" ")
            for i in range(0, len(terms)): terms[i] = self.fixCase(terms[i])
            async with aiohttp.ClientSession() as session:
                async with session.get("http://gbf.wiki/{}".format("_".join(terms))) as r:
                    if r.status != 200:
                        raise Exception("HTTP Error 404: Not Found")
                    else:
                        soup = BeautifulSoup(await r.read(), 'html.parser')
                        thumbnail = "http://game-a1.granbluefantasy.jp/assets_en/img_low/sp/assets/summon/m/{}.jpg".format(soup.find_all("div", class_="mw-parser-output")[0].findChildren("div" , recursive=False)[0].findChildren("div" , recursive=False)[0].findChildren("div" , recursive=False)[1].findChildren("div" , recursive=False)[0].findChildren("div" , recursive=False)[1].findChildren("table" , recursive=False)[0].findChildren("tbody" , recursive=False)[0].findChildren("tr" , recursive=False)[1].findChildren("td" , recursive=False)[0].text.replace(" ", ""))
        except:
            thumbnail = ""

        history = []
        for u in data:
            if u[0] not in history:
                history.append(u[0])
                self.cursor.execute("SELECT * FROM players WHERE id == {}".format(u[0]))
                pname = self.cursor.fetchall()
                if len(pname) == 0: continue
                if count < 3:
                    fields.append({'name':'Page {} '.format(self.bot.getEmote(str(len(fields)+1))), 'value':'', 'inline':True})
                fields[count%3]['value'] += "**{}**▫️[{}](http://game.granbluefantasy.jp/#profile/{})\n".format(u[1], self.escape(pname[0][1]), u[0])
                count += 1
                if count >= 30:
                    if level > 0: msg = "*Only {} random results shown*.".format(count)
                    else: msg = "*Only {} random results shown, specify a minimum level to affine the result*.".format(count)
                    break

        if count == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Summon Error", description="`{}` ▫️ No one has this summon above level {}".format(name, level), footer="Be sure to type the full name", thumbnail=thumbnail, color=self.color))
        else:
            if level > 0:
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"{} ▫️ Lvl {} and more".format(name.capitalize(), level), 'icon_url':thumbnail}, description=msg, fields=fields, footer="Auto updated once per week", color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"{}".format(name.capitalize()), 'icon_url':thumbnail}, description=msg, fields=fields, footer="Auto updated once per week", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['id'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def profile(self, ctx, *target : str):
        """Retrieve a GBF profile"""
        target = " ".join(target)
        try:
            cog = self.bot.get_cog('Baguette')
            if cog is None: return
            if target == "":
                if str(ctx.author.id) not in self.bot.gbfids:
                    await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(ctx.author.display_name), footer="setProfile <id>", color=self.color))
                    return
                id = self.bot.gbfids[str(ctx.author.id)]
            elif target.startswith('<@') and target.endswith('>'):
                try:
                    if target[2] == "!": target = int(target[3:-1])
                    else: target = int(target[2:-1])
                    member = ctx.guild.get_member(target)
                    if str(member.id) not in self.bot.gbfids:
                        await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.gbfids[str(member.id)]
                except:
                    await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid parameter {} -> {}".format(target, type(target)), color=self.color))
                    return
            else:
                try: id = int(target)
                except:
                    member = ctx.guild.get_member_named(target)
                    if member is None:
                        await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Member not found", color=self.color))
                        return
                    elif str(member.id) not in self.bot.gbfids:
                        await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.gbfids[str(member.id)]
            if id < 0 or id >= 100000000:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
            data = await cog.getProfileData(id)
            if data == "Maintenance":
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Game is in maintenance", color=self.color))
                return
            elif data is None:
                self.badprofilecache.append(id)
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
            soup = BeautifulSoup(data, 'html.parser')
            try: name = soup.find_all("span", class_="txt-other-name")[0].string
            except: name = None
            if name is not None:
                header = None
                rarity = "R"
                possible_headers = [("prt-title-bg-gld", "SSR"), ("prt-title-bg-slv", "SR"), ("prt-title-bg-nml", "R"), ("prt-title-bg-cpr", "R")]
                for h in possible_headers:
                    try:
                        header = soup.find_all("div", class_=h[0])[0]
                        rarity = h[1]
                    except:
                        pass
                if header is not None: rank = "**{}**".format(self.rankre.search(str(header)).group(0))
                else:
                    await self.bot.send('debug', 'profile: debug this profile: {}'.format(id))
                    rank = ""
                trophy = soup.find_all("div", class_="prt-title-name")[0].string
                comment = su.unescape(soup.find_all("div", class_="prt-other-comment")[0].string).replace('\t', '').replace('\n', '')
                if comment == "": pass
                elif rank == "": comment = "💬 ``{}``".format(comment)
                else: comment = " ▫️ 💬 ``{}``".format(comment)
                mc_url = soup.find_all("img", class_="img-pc")[0]['src'].replace("/po/", "/talk/").replace("/img_low/", "/img/")
                stats = soup.find_all("div", class_="num")
                hp = int(stats[0].string)
                atk = int(stats[1].string)
                job = soup.find_all("div", class_="txt-other-job-info")[0].string
                job_lvl = soup.find_all("div", class_="txt-other-job-level")[0].string.replace("  ", " ")

                try:
                    try:
                        crew = soup.find_all("div", class_="prt-guild-name")[0].string
                        crewid = soup.find_all("div", class_="btn-guild-detail")[0]['data-location-href']
                        crew = "[{}](http://game.granbluefantasy.jp/#{})".format(crew, crewid)
                    except: crew = soup.find_all("div", class_="txt-notjoin")[0].string
                except:
                    crew = None

                # get the last gw score
                cog = self.bot.get_cog('GW')
                scores = ""
                if cog is not None:
                    pdata = await cog.searchGWDBPlayer(ctx, id, 2)
                    if pdata is not None:
                        for n in range(0, 2):
                            if pdata[n] is not None and 'result' in pdata[n] and len(pdata[n]['result']) == 1:
                                try:
                                    if pdata[n]['result'][0][0] is None:
                                        scores += "{} GW**{}** ▫️ **{:,}** honors\n".format(self.bot.getEmote('gw'), pdata[n].get('gw', ''), pdata[n]['result'][0][3])
                                    else:
                                        scores += "{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors\n".format(self.bot.getEmote('gw'), pdata[n].get('gw', ''), pdata[n]['result'][0][0], pdata[n]['result'][0][3])
                                except:
                                    pass

                fields = []

                try:
                    summons_res = self.sumre.findall(data)
                    summons = {}
                    for s in summons_res:
                        summons[s[0]] = s[1]
                    count = 0
                    half = len(summons) // 2
                    if half < 4: half = 4
                    msg = ""
                    for s in self.possiblesum:
                        if s in summons:
                            msg += "{} {}\n".format(self.bot.getEmote(self.possiblesum[s]), summons[s])
                            count += 1
                            if count == half and msg != "":
                                fields.append({'name':'{} Summons'.format(self.bot.getEmote('summon')), 'value':msg, 'inline':True})
                                msg = ""
                    if msg != "":
                        fields.append({'name':'{} Summons'.format(self.bot.getEmote('summon')), 'value':msg, 'inline':True})
                except:
                    pass

                try:
                    beg = data.find('<div class="prt-inner-title">Star Character</div>')
                    end = data.find('<div class="prt-2tabs">', beg+1)
                    star_section = data[beg:end]
                    try:
                        ring = self.starringre.findall(star_section)[0]
                        msg = "**\💍** "
                    except:
                        msg = ""
                    msg += "{}".format(self.starre.findall(star_section)[0]) # name
                    try: msg += " **{}**".format(self.starplusre.findall(star_section)[0]) # plus
                    except: pass
                    try: msg += " ▫️ **{}** EMP".format(self.empre.findall(star_section)[0]) # emp
                    except: pass
                    starcom = self.starcomre.findall(star_section)
                    if starcom is not None and starcom[0] != "(Blank)": msg += "\n\u202d💬 ``{}``".format(su.unescape(starcom[0]))
                    fields.append({'name':'{} Star Character'.format(self.bot.getEmote('skill2')), 'value':msg})
                except:
                    pass
                if trophy == "No Trophy Displayed": title = "\u202d{} **{}**".format(self.bot.getEmote(rarity), name)
                else: title = "\u202d{} **{}**▫️{}".format(self.bot.getEmote(rarity), name, trophy)

                await ctx.send(embed=self.bot.buildEmbed(title=title, description="{}{}\n{} Crew ▫️ {}\n{}".format(rank, comment, self.bot.getEmote('gw'), crew, scores), fields=fields, thumbnail=mc_url, url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile is private", url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
                return

        except Exception as e:
            await self.bot.sendError("profile", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def crew(self, ctx, *id : str):
        """Get a crew profile"""
        await self.postCrewData(ctx, id)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['contrib', 'contri', 'leeches', 'contribs', 'contris', 'contributions'])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def contribution(self, ctx, *id : str):
        """Get a crew profile (GW scores are force-enabled)"""
        await self.postCrewData(ctx, id, 2)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['ticket'])
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def upcoming(self, ctx, jp : str = ""):
        """Post the upcoming gacha(s)"""
        try:
            cog = self.bot.get_cog('Baguette')
            if cog is None: return
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
            meat_per_ex_average = 2
            meat = 0
            total_meat = 0
            nm = [0, 0]
            day_target = [target * 0.15, target * 0.35]
            meat_use = [5, 20]
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

            await ctx.send(embed=self.bot.buildEmbed(title="{} Honor Planning ▫️ {} honors".format(self.bot.getEmote('gw'), self.honorFormat(target)), description="Preliminaries & Interlude ▫️ **{:,}** meats (around **{:,}** EX+ and **{:}** honors)\nDay 1 and 2 each ▫️ **{:,}** NM95 (**{:}** honors)\nDay 3 and 4 each ▫️ **{:,}** NM150 (**{:}** honors)".format(math.ceil(total_meat*2), ex*2, self.honorFormat(honor[0]*2), nm[0]*2, self.honorFormat(honor[1]*2), nm[1]*2, self.honorFormat(honor[2]*2)), footer="Assuming {} meats / EX+ on average".format(meat_per_ex_average), color=self.color))
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