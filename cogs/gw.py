import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import json
import sqlite3

class GW(commands.Cog):
    """GW related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xf4426e
        self.sql = None
        self.conn = None
        self.cursor = None

    def startTasks(self):
        self.bot.runTask('check_ranking', self.checkGWRanking)
        self.bot.runTask('check_buff', self.checkGWBuff)

    async def checkGWRanking(self):
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="checkgwranking() started", timestamp=datetime.utcnow()))

        cog = self.bot.get_cog('Baguette')
        if cog is None:
            return
        crews = [2000, 5500, 9000, 14000, 18000, 30000]
        players = [2000, 50000, 100000, 160000, 250000, 350000]

        days = ["End", "Day 5", "Day 4", "Day 3", "Day 2", "Day 1", "Interlude", "Preliminaries"]
        minute_update = [5, 25, 45]

        while True:
            self.getGWState()
            try:
                if self.bot.gw['state'] == False:
                    self.bot.gw['ranking'] = None
                    self.bot.savePending = True
                    await asyncio.sleep(3600)
                elif self.bot.getJST() < self.bot.gw['dates']["Preliminaries"]:
                    self.bot.gw['ranking'] = None
                    self.bot.savePending = True
                    d = self.bot.gw['dates']["Preliminaries"] - self.bot.getJST()
                    await asyncio.sleep(d.seconds + 1)
                elif self.bot.getJST() > self.bot.gw['dates']["Day 5"] - timedelta(seconds=21600):
                    await asyncio.sleep(3600)
                else:
                    if not self.checkMaintenance():
                        current_time = self.bot.getJST()
                        m = current_time.minute
                        h = current_time.hour
                        skip = False
                        for d in days:
                            if current_time < self.bot.gw['dates'][d]:
                                continue
                            elif(d == "Preliminaries" and current_time > self.bot.gw['dates']["Interlude"] - timedelta(seconds=24000)) or (d.startswith("Day") and h < 7 and h >= 2) or d == "Day 5":
                                skip = True
                            break
                        if skip:
                            await asyncio.sleep(600)
                        elif m in minute_update:
                            try:
                                data = [{}, {}, {}, {}, current_time - timedelta(seconds=60 * (current_time.minute % 20))]
                                if self.bot.gw['ranking'] is not None:
                                    diff = data[4] - self.bot.gw['ranking'][4]
                                    diff = round(diff.total_seconds() / 60.0)
                                else: diff = 0
                                for c in crews:
                                    r = await cog.requestRanking(c // 10, True)
                                    if r is not None and 'list' in r and len(r['list']) > 0:
                                        data[0][str(c)] = int(r['list'][-1]['point'])
                                        if diff > 0 and self.bot.gw['ranking'] is not None and str(c) in self.bot.gw['ranking'][0]:
                                            data[2][str(c)] = (data[0][str(c)] - self.bot.gw['ranking'][0][str(c)]) / diff
                                    await asyncio.sleep(0.001)

                                for p in players:
                                    r = await cog.requestRanking(p // 10, False)
                                    if r is not None and 'list' in r and len(r['list']) > 0:
                                        data[1][str(p)] = int(r['list'][-1]['point'])
                                        if diff > 0 and self.bot.gw['ranking'] is not None and str(p) in self.bot.gw['ranking'][1]:
                                            data[3][str(p)] = (data[1][str(p)] - self.bot.gw['ranking'][1][str(p)]) / diff
                                    await asyncio.sleep(0.001)

                                self.bot.gw['ranking'] = data
                                self.bot.savePending = True
                            except Exception as ex:
                                await self.bot.sendError('checkgwranking', str(ex))
                                self.bot.gw['ranking'] = None
                                self.bot.savePending = True
                            await asyncio.sleep(600)
                        else:
                            await asyncio.sleep(30)
                    else:
                        await asyncio.sleep(60)
            except asyncio.CancelledError:
                await self.bot.sendError('checkgwranking', 'cancelled')
                await asyncio.sleep(30)
            except Exception as e:
                await self.bot.sendError('checkgwranking', str(e))
                return

    async def checkGWBuff(self): # automatically calls the GW buff used by the (you) crew
        self.getGWState()
        if self.bot.gw['state'] == False: return
        await asyncio.sleep(3)
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="checkgwbuff() started", timestamp=datetime.utcnow()))
        try:
            guild = self.bot.get_guild(self.bot.ids['you_server'])
            if guild is None:
                await self.bot.sendError('checkgwbuff', 'cancelled, no guild found')
            channel = self.bot.get_channel(self.bot.ids['you_announcement'])
            gl_role = guild.get_role(self.bot.ids['gl'])
            fo_role = guild.get_role(self.bot.ids['fo'])
            buff_role = [[guild.get_role(self.bot.ids['atkace']), 'atkace'], [guild.get_role(self.bot.ids['deface']), 'deface']]
            msg = ""
            while self.bot.gw['state'] and (len(self.bot.gw['buffs']) > 0 or len(msg) != 0):
                current_time = self.bot.getJST() + timedelta(seconds=32)
                if len(self.bot.gw['buffs']) > 0 and current_time >= self.bot.gw['buffs'][0][0]:
                    msg = ""
                    if (current_time - self.bot.gw['buffs'][0][0]) < timedelta(seconds=200):
                        if self.bot.gw['buffs'][0][1]:
                            for r in buff_role:
                                msg += "{} {} ".format(self.bot.getEmote(r[1]), r[0].mention)
                        if self.bot.gw['buffs'][0][2]:
                            msg += "{} {} ".format(self.bot.getEmote('foace'), fo_role.mention)
                        if self.bot.gw['buffs'][0][4]:
                            if self.bot.gw['buffs'][0][3]:
                                msg += 'buffs in 5 minutes **(Please use both this time only !)**'
                            else:
                                msg += 'buffs now! **(Please use both this time only !)**'
                        else:
                            if self.bot.gw['buffs'][0][3]:
                                msg += 'buffs in 5 minutes'
                            else:
                                msg += 'buffs now!'
                        if self.bot.gw['skip']:
                            msg = ""
                        if not self.bot.gw['buffs'][0][3]:
                            self.bot.gw['skip'] = False
                    self.bot.gw['buffs'].pop(0)
                    self.bot.savePending = True
                else:
                    if msg != "":
                        await channel.send("{} {}".format(gl_role.mention, msg))
                        msg = ""
                    if len(self.bot.gw['buffs']) > 0:
                        d = self.bot.gw['buffs'][0][0] - current_time
                        if d.seconds > 1:
                            await asyncio.sleep(d.seconds-1)
            if len(msg) > 0:
                await channel.send(msg)
        except asyncio.CancelledError:
            await self.bot.sendError('checkgwbuff', 'cancelled')
        except Exception as e:
            await self.bot.sendError('checkgwbuff', str(e))
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="checkgwbuff() ended", timestamp=datetime.utcnow()))

    def checkMaintenance(self):
        try:
            return self.bot.get_cog('GBF_Utility').checkMaintenance()
        except:
            return False

    def buildDayList(self): # used by the gw schedule command
        return [
            ["{} Ban Wave".format(self.bot.getEmote('kmr')), "BW", ""],
            ["{} Preliminaries".format(self.bot.getEmote('gold')), "Preliminaries", "Interlude"],
            ["{} Interlude".format(self.bot.getEmote('wood')), "Interlude", "Day 1"],
            ["{} Day 1".format(self.bot.getEmote('1')), "Day 1", "Day 2"],
            ["{} Day 2".format(self.bot.getEmote('2')), "Day 2", "Day 3"],
            ["{} Day 3".format(self.bot.getEmote('3')), "Day 3", "Day 4"],
            ["{} Day 4".format(self.bot.getEmote('4')), "Day 4", "Day 5"],
            ["{} Final Rally".format(self.bot.getEmote('red')), "Day 5", "End"]
        ]

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def isYouServer(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isYouServer(ctx)
        return commands.check(predicate)

    def isAuthorizedSpecial(): # for decorators
        async def predicate(ctx):
            return (ctx.bot.isYouServer(ctx) or ctx.bot.isAuthorized(ctx))
        return commands.check(predicate)

    def dayCheck(self, current, day, final_day=False):
        d = day - current
        if current < day and (final_day or d >= timedelta(seconds=25200)):
            return True
        return False

    def getGWState(self): # return the current state of the guild war in string format (which day is on going, etc...)
        if self.bot.gw['state'] == True:
            current_time = self.bot.getJST()
            if current_time < self.bot.gw['dates']["Preliminaries"]:
                d = self.bot.gw['dates']["Preliminaries"] - current_time
                return "{} Guild War starts in **{}**".format(self.bot.getEmote('time'), self.bot.getTimedeltaStr(d, True))
            elif current_time >= self.bot.gw['dates']["End"]:
                self.bot.gw['state'] = False
                self.bot.gw['dates'] = {}
                self.bot.cancelTask('gwtask')
                self.bot.savePending = True
                return ""
            elif current_time > self.bot.gw['dates']["Day 5"]:
                d = self.bot.gw['dates']["End"] - current_time
                return "{} Final Rally is on going\n{} Guild War ends in **{}**".format(self.bot.getEmote('mark_a'), self.bot.getEmote('time'), self.bot.getTimedeltaStr(d))
            elif current_time > self.bot.gw['dates']["Day 1"]:
                it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
                for i in range(1, len(it)): # loop to not copy paste this 5 more times
                    if current_time > self.bot.gw['dates'][it[i]]:
                        d = self.bot.gw['dates'][it[i-1]] - current_time
                        if d < timedelta(seconds=25200): msg = "{} {} ended".format(self.bot.getEmote('mark_a'), it[i])
                        else: msg = "{} {} is on going (Time left: **{}**)".format(self.bot.getEmote('mark_a'), it[i], self.bot.getTimedeltaStr(self.bot.gw['dates'][it[i]] + timedelta(seconds=61200) - current_time))
                        if i == 1: return "{}\n{} {} starts in **{}**".format(msg, self.bot.getEmote('time'), it[i-1].replace('Day 5', 'Final Rally'), self.bot.getTimedeltaStr(d))
                        else: return "{}\n{} {} starts in **{}**".format(msg,self.bot.getEmote('time'), it[i-1], self.bot.getTimedeltaStr(d) )
            elif current_time > self.bot.gw['dates']["Interlude"]:
                d = self.bot.gw['dates']["Day 1"] - current_time
                return "{} Interlude is on going\n{} Day 1 starts in **{}**".format(self.bot.getEmote('mark_a'), self.bot.getEmote('time'), self.bot.getTimedeltaStr(d))
            elif current_time > self.bot.gw['dates']["Preliminaries"]:
                d = self.bot.gw['dates']['Interlude'] - current_time
                if d < timedelta(seconds=25200): msg = "{} Preliminaries ended".format(self.bot.getEmote('mark_a'))
                else: msg = "{} Preliminaries are on going (Time left: **{}**)".format(self.bot.getEmote('mark_a'), self.bot.getTimedeltaStr(self.bot.gw['dates']["Preliminaries"] + timedelta(seconds=104400) - current_time, True))
                return "{}\n{} Interlude starts in **{}**".format(msg, self.bot.getEmote('time'), self.bot.getTimedeltaStr(d, True))
            else:
                return ""
        else:
            return ""

    def getNextBuff(self, ctx): # for the (you) crew, get the next set of buffs to be called
        if self.bot.gw['state'] == True and ctx.guild.id == self.bot.ids['you_server']:
            current_time = self.bot.getJST()
            if current_time < self.bot.gw['dates']["Preliminaries"]:
                return ""
            for b in self.bot.gw['buffs']:
                if not b[3] and current_time < b[0]:
                    msg = "{} Next buffs in **{}** (".format(self.bot.getEmote('question'), self.bot.getTimedeltaStr(b[0] - current_time, True))
                    if b[1]:
                        msg += "Attack {}, Defense {}".format(self.bot.getEmote('atkace'), self.bot.getEmote('deface'))
                        if b[2]:
                            msg += ", FO {}".format(self.bot.getEmote('foace'))
                    elif b[2]:
                        msg += "FO {}".format(self.bot.getEmote('foace'))
                    msg += ")"
                    return msg
        return ""

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def GW(self, ctx):
        """Post the GW schedule"""
        if self.bot.gw['state'] == True:
            try:
                current_time = self.bot.getJST()
                title = "{} **Guild War {}** :white_small_square: Time: **{:%a. %m/%d %H:%M}**\n".format(self.bot.getEmote('gw'), self.bot.gw['id'], current_time)
                description = ""
                day_list = self.buildDayList()
                if current_time < self.bot.gw['dates']["End"]:
                    for it in day_list:
                        if it[1] == "BW":
                            d = self.bot.gw['dates']["Preliminaries"] - timedelta(days=random.randint(1, 4))
                            if current_time < d and random.randint(1, 8) == 1:
                                description += it[0] + " **{:%a. %m/%d %H:%M}**\n".format(d)
                        else:
                            if self.dayCheck(current_time, self.bot.gw['dates'][it[2]], it[1]=="Day 5") or (it[1] == "Interlude" and self.dayCheck(current_time, self.bot.gw['dates'][it[2]] + timedelta(seconds=25200), False)):
                                description += it[0] + ": **{:%a. %m/%d %H:%M}**\n".format(self.bot.gw['dates'][it[1]])
                else:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Not available", color=self.color))
                    self.bot.gw['state'] = False
                    self.bot.gw['dates'] = {}
                    self.bot.cancelTask('gwtask')
                    self.bot.savePending = True
                    return

                try:
                    description += self.getGWState()
                except Exception as e:
                    await self.bot.sendError("getgwstate", str(e))

                try:
                    description += '\n' + self.getNextBuff(ctx)
                except Exception as e:
                    await self.bot.sendError("getnextbuff", str(e))

                await ctx.send(embed=self.bot.buildEmbed(title=title, description=description, color=self.color))
            except Exception as e:
                await self.bot.sendError("gw", str(e))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Not available", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwtime'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def fugdidgwstart(self, ctx):
        """Check if GW started"""
        try:
            d = self.getGWState()
            if d != "":
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** :white_small_square: status".format(self.bot.getEmote('gw'), self.bot.gw['id']), description=d, color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("fugdidgwstart", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['buff'])
    @isYouServer()
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def GWbuff(self, ctx):
        """Check when is the next GW buff, (You) Only"""
        try:
            d = self.getNextBuff(ctx)
            if d != "":
                await ctx.send(embed=self.bot.buildEmbed(title="{} Guild War (You) Buff status".format(self.bot.getEmote('gw')), description=d, color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="{} Guild War (You) Buff status".format(self.bot.getEmote('gw')), description="Only available when Guild War is on going", color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("gwbuff", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['searchcrew'])
    @isAuthorizedSpecial()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def search(self, ctx, *, terms : str):
        """Search a crew preliminary score (by name)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://gbf.gw.lt/gw-guild-searcher/search", json={'search': terms}) as resp:
                    if resp.status != 200: raise Exception("HTTP Error " + str(resp.status))
                    data = json.loads(await resp.read())
            if len(data['result']) == 1:
                try:
                    await self.bot.callCommand(ctx, 'searchID', 'GW', data['result'][0]['id'])
                    return
                except:
                    pass
            embed = discord.Embed(title="{} Guild Searcher".format(self.bot.getEmote('gw')), url="http://gbf.gw.lt/gw-guild-searcher/search", color=self.color) # random color
            embed.set_footer(text="crew history: searchid <crew id>")
            i = 0
            for c in data['result']:
                msg = "GW**{}** score: **{:,}".format(c['data'][0]['gw_num'], c['data'][0]['points'])
                if c['data'][0]['is_seed']: msg += " (seeded)"
                msg += "**"
                embed.add_field(name="{} ▫️ {}".format(c["data"][0]["name"], msg), value="http://game.granbluefantasy.jp/#guild/detail/{}".format(c['id']), inline=False)
                i += 1
                if i >= 5: break
            if len(data["result"]) > 5: 
                embed.add_field(name="5 / {} results shown".format(len(data["result"])), value="please go here for more: http://gbf.gw.lt/gw-guild-searcher/", inline=False)
            if i > 0: await ctx.send(embed=embed)
            else: await ctx.send(embed=self.bot.buildEmbed(title="{} Guild Searcher".format(self.bot.getEmote('gw')), description="No Crews found", color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="The seach couldn't be completed", footer=str(e), color=self.color))
            await self.bot.sendError("search", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorizedSpecial()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def searchID(self, ctx, id : int):
        """Search a crew preliminary score (by ID)"""
        try:
            if id < 0: raise Exception("Negative ID")
            async with aiohttp.ClientSession() as session:
                async with session.get("http://gbf.gw.lt/gw-guild-searcher/info/{}".format(id)) as resp:
                    if resp.status != 200: raise Exception("HTTP Error " + str(resp.status))
                    data = json.loads(await resp.read())
            if len(data["data"]) == 0:
                await ctx.send(embed=self.bot.buildEmbed(title="{} Guild Searcher".format(self.bot.getEmote('gw')), description="Crew not found", color=self.color))
                return
            embed = discord.Embed(title="{} Guild Searcher".format(self.bot.getEmote('gw')), url="http://gbf.gw.lt/gw-guild-searcher/search", description="{} ▫️ http://game.granbluefantasy.jp/#guild/detail/{}".format(data["data"][0]["name"], data["id"]), color=random.randint(0, 16777216)) # random color
            i = 0
            for c in data["data"]:
                msg = "score: **{:,}".format(c["points"])
                if c["is_seed"]: msg += " (seeded)**"
                else: msg += "**"
                embed.add_field(name="GW{}".format(c["gw_num"]), value=msg, inline=True)
                i += 1
                if i >= 6: break
            if len(data["data"]) > 6: 
                embed.add_field(name="6 / {} past GWs shown".format(len(data["data"])), value="please go here for more: http://gbf.gw.lt/gw-guild-searcher/", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="The seach couldn't be completed", footer=str(e), color=self.color))
            await self.bot.sendError("searchid", str(e))


    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rankings', 'cutoff', 'cutoffs'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def ranking(self, ctx):
        """Retrieve the current GW ranking"""
        try:
            if self.bot.gw['state'] == False or self.bot.getJST() < self.bot.gw['dates']["Preliminaries"] or self.bot.gw['ranking'] is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Ranking unavailable", color=self.color))
            else:
                fields = [{'name':'**Crew Ranking**', 'value':''}, {'name':'**Player Ranking**', 'value':''}]
                for c in self.bot.gw['ranking'][0]:
                    fields[0]['value'] += "**#{:,}K** \▫️ {:,}".format(int(c)//1000, self.bot.gw['ranking'][0][c])
                    if c in self.bot.gw['ranking'][2]:
                        if self.bot.gw['ranking'][2][c] > 1000000000:
                            fields[0]['value'] += " \▫️  {:,.1f}B/min".format(self.bot.gw['ranking'][2][c]/1000000000)
                        elif self.bot.gw['ranking'][2][c] > 1000000:
                            fields[0]['value'] += " \▫️  {:,.1f}M/min".format(self.bot.gw['ranking'][2][c]/1000000)
                        elif self.bot.gw['ranking'][2][c] > 1000:
                            fields[0]['value'] += " \▫️  {:,.1f}K/min".format(self.bot.gw['ranking'][2][c]/1000)
                        elif self.bot.gw['ranking'][2][c] > 0:
                            fields[0]['value'] += " \▫️  {:,.1f}/min".format(self.bot.gw['ranking'][2][c])
                    fields[0]['value'] += "\n"
                if fields[0]['value'] == '': fields[0]['value'] = 'Unaivalable'

                for c in self.bot.gw['ranking'][1]:
                    fields[1]['value'] += "**#{:,}K** \▫️ {:,}".format(int(c)//1000, self.bot.gw['ranking'][1][c])
                    if c in self.bot.gw['ranking'][3]:
                        if self.bot.gw['ranking'][3][c] > 1000000000:
                            fields[1]['value'] += " \▫️  {:,.1f}B/min".format(self.bot.gw['ranking'][3][c]/1000000000)
                        elif self.bot.gw['ranking'][3][c] > 1000000:
                            fields[1]['value'] += " \▫️  {:,.1f}M/min".format(self.bot.gw['ranking'][3][c]/1000000)
                        elif self.bot.gw['ranking'][3][c] > 1000:
                            fields[1]['value'] += " \▫️  {:,.1f}K/min".format(self.bot.gw['ranking'][3][c]/1000)
                        elif self.bot.gw['ranking'][3][c] > 0:
                            fields[1]['value'] += " \▫️  {:,.1f}/min".format(self.bot.gw['ranking'][3][c])
                    fields[1]['value'] += "\n"
                if fields[1]['value'] == '': fields[1]['value'] = 'Unaivalable'

                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), self.bot.gw['id']), fields=fields, footer="Last Update ▫️ {:%a. %m/%d %H:%M} JST ▫️ Update on minute 5, 25 and 45".format(self.bot.gw['ranking'][4]), inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("ranking", str(e))

    async def loadGWDB(self):
        try:
            if self.bot.drive.dlFile("GW.sql", self.bot.tokens['files']):
                self.conn = sqlite3.connect("GW.sql")
                self.cursor = self.conn.cursor()
                self.sql = True
            else:
                self.sql = False
        except Exception as e:
            self.sql = None
            await self.bot.sendError('loadGWDB', str(e))
        return self.sql

    async def searchGWDB(self, ctx, terms, mode):
        if self.sql is None:
            await self.bot.react(ctx, 'time')
            await self.loadGWDB()
            await self.bot.unreact(ctx, 'time')

        if self.sql is None or self.sql == False:
            return None

        data = {}
        try:
            self.cursor.execute("SELECT id FROM GW")
            for row in self.cursor:
                data['gw'] = int(row[0])
                break
        except:
            pass

        try:
            if mode == 0:
                self.cursor.execute("SELECT * FROM crews WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\%")))
            elif mode == 1:
                self.cursor.execute("SELECT * FROM crews WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\%")))
            elif mode == 2:
                self.cursor.execute("SELECT * FROM crews WHERE id = {}".format(terms))
            data['result'] = self.cursor.fetchall()
            random.shuffle(data['result'])
            return data
        except Exception as e:
            await self.bot.sendError('searchGWDB', str(e))
            return {}

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def reloadDB(self, ctx):
        """Download GW.sql (Owner only)"""
        await self.bot.react(ctx, 'time')
        await self.loadGWDB()
        await self.bot.unreact(ctx, 'time')
        if self.sql is None or self.sql == False:
            await ctx.message.add_reaction('❎') # white negative mark
        else:
            await ctx.message.add_reaction('✅') # white check mark


    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwcrew'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def findcrew(self, ctx, *, terms : str = ""):
        """Search a crew GW score in the bot data
        add %id to search by id or %eq to get an exact match
        add %all to receive by dm all results"""
        if terms == "":
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="**Usage**\n`findcrew [crewname]` to search a crew by name\n`findcrew %eq [crewname]` or `findcrew %== [crewname]` for an exact match\n`findcrew %id [crewid]` for an id search\n`findcrew %all ...` to receive all the results by direct message".format(terms), color=self.color))
            return

        index = terms.find("%all ")
        if index != -1 and index + 5 < len(terms):
            terms = terms.replace("%all ", "")
            all = True
        else:
            all = False

        if terms.startswith("%== ") or terms.startswith("%eq "):
            terms = terms[4:]
            mode = 1
        elif terms.startswith("%id "):
            try:
                terms = int(terms[4:])
                mode = 2
            except:
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                return
        else:
            mode = 0
        data = await self.searchGWDB(ctx, terms, mode)
        if data is None:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
            return
        gwnum = data.get('gw', '')
        result = data.get('result', [])

        if len(result) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` not found".format(terms), color=self.color))
            return
        elif all:
            x = len(result)
            if x > 20: x = 20
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Sending your {}/{} result(s)".format(x, len(result)), color=self.color))
        elif len(result) > 3: x = 3
        elif len(result) > 1: x = len(result)
        else: x = 1

        fields = []
        for i in range(0, x):
            fields.append({'name':"{}▫️{}".format(result[i][2], result[i][1]), 'value':''})
            if result[i][0] is not None: fields[-1]['value'] += "**#{}**\n".format(result[i][0])
            if result[i][3] is not None: fields[-1]['value'] += "**P.** ▫️{:,}\n".format(result[i][3])
            if result[i][4] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('1'), result[i][4])
            if result[i][6] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('2'), result[i][6])
            if result[i][8] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('3'), result[i][8])
            if result[i][10] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('4'), result[i][10])
            if fields[-1]['value'] == "": fields[-1]['value'] = "No data"
            if all:
                try:
                    await ctx.author.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), fields=fields, inline=True, color=self.color))
                except:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="I can't send you the full list by private messages", color=self.color))
                    return
                fields = []

        if all:
            await ctx.message.add_reaction('✅') # white check mark
            return
        elif len(result) > 3: desc = "3/{} random result(s) shown".format(len(result))
        else: desc = ""

        await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), description=desc, fields=fields, inline=True, color=self.color))