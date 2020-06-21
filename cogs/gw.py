import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import json
import sqlite3
from xml.sax import saxutils as su

class GW(commands.Cog):
    """GW related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xf4426e
        self.sql = [None, None]
        self.conn = [None, None]
        self.cursor = [None, None]
        self.loadingdb = False

    def startTasks(self):
        self.bot.runTask('check_ranking', self.checkGWRanking)
        self.bot.runTask('check_buff', self.checkGWBuff)

    async def checkGWRanking(self):
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="checkgwranking() started", timestamp=datetime.utcnow()))

        cog = self.bot.get_cog('Baguette')
        if cog is None:
            return
        crewsA = [300, 1000, 2000, 8000, 19000, 30000]
        crewsB = [2000, 5500, 9000, 14000, 18000, 30000]
        players = [2000, 70000, 120000, 160000, 250000, 350000]

        days = ["End", "Day 5", "Day 4", "Day 3", "Day 2", "Day 1", "Interlude", "Preliminaries"]
        minute_update = [4, 24, 44]

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
                    if not await self.checkMaintenance():
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
                            if d.startswith("Day "):
                                crews = crewsB
                            else:
                                crews = crewsA
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
            guild = self.bot.get_guild(self.bot.ids.get('you_server', 0))
            if guild is None:
                await self.bot.sendError('checkgwbuff', 'cancelled, no guild found')
            channel = self.bot.get_channel(self.bot.ids.get('you_announcement', 0))
            gl_role = guild.get_role(self.bot.ids.get('gl', 0))
            fo_role = guild.get_role(self.bot.ids.get('fo', 0))
            buff_role = [[guild.get_role(self.bot.ids.get('atkace', 0)), 'atkace'], [guild.get_role(self.bot.ids.get('deface', 0)), 'deface']]
            msg = ""
            while self.bot.gw['state'] and (len(self.bot.gw['buffs']) > 0 or len(msg) != 0):
                current_time = self.bot.getJST() + timedelta(seconds=32)
                if len(self.bot.gw['buffs']) > 0 and current_time >= self.bot.gw['buffs'][0][0]:
                    msg = ""
                    if (current_time - self.bot.gw['buffs'][0][0]) < timedelta(seconds=200):
                        if self.bot.gw['buffs'][0][1]:
                            for r in buff_role:
                                msg += "{} {}\n".format(self.bot.getEmote(r[1]), r[0].mention)
                        if self.bot.gw['buffs'][0][2]:
                            msg += "{} {}\n".format(self.bot.getEmote('foace'), fo_role.mention)
                        if self.bot.gw['buffs'][0][4]:
                            if self.bot.gw['buffs'][0][3]:
                                msg += '*Buffs in 5 minutes* **(Double use this time only !)**'
                            else:
                                msg += 'Buffs now! **(Double use this time only !)**'
                        else:
                            if self.bot.gw['buffs'][0][3]:
                                msg += '*Buffs in 5 minutes*'
                            else:
                                msg += 'Buffs now!'
                        if self.bot.gw['skip']:
                            msg = ""
                        if not self.bot.gw['buffs'][0][3]:
                            self.bot.gw['skip'] = False
                    self.bot.gw['buffs'].pop(0)
                    self.bot.savePending = True
                else:
                    if msg != "":
                        await channel.send("{} {}\n{}".format(self.bot.getEmote('captain'), gl_role.mention, msg))
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

    async def checkMaintenance(self):
        try:
            return not await self.bot.get_cog('GBF_Utility').isGBFAvailable()
        except:
            return True

    def buildDayList(self): # used by the gw schedule command
        return [
            ["{} Automatic BAN Execution".format(self.bot.getEmote('kmr')), "BW", ""],
            ["{} Preliminaries".format(self.bot.getEmote('gold')), "Preliminaries", "Interlude"],
            ["{} Interlude".format(self.bot.getEmote('wood')), "Interlude", "Day 1"],
            ["{} Day 1".format(self.bot.getEmote('1')), "Day 1", "Day 2"],
            ["{} Day 2".format(self.bot.getEmote('2')), "Day 2", "Day 3"],
            ["{} Day 3".format(self.bot.getEmote('3')), "Day 3", "Day 4"],
            ["{} Day 4".format(self.bot.getEmote('4')), "Day 4", "Day 5"],
            ["{} Final Rally".format(self.bot.getEmote('red')), "Day 5", "End"]
        ]

    def escape(self, s): # escape markdown string
        # add the RLO character before
        return '\u202d' + s.replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('[', '').replace(']', '').replace('(', '\\(').replace(')', '\\)').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('|', '\\|')

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

    def honor(self, h): # convert honor number to a shorter string version
        if h is None: return "n/a"
        else:
            try:
                h = int(h)
            except:
                return h
            if h >= 1000000000: return "{:.1f}B".format(h/1000000000)
            elif h >= 1000000: return "{:.1f}M".format(h/1000000)
            elif h >= 1000: return "{:.1f}K".format(h/1000)
        return h

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
                        else: return "{}\n{} {} starts in **{}**".format(msg, self.bot.getEmote('time'), it[i-1], self.bot.getTimedeltaStr(d))
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

    def getGWTimeLeft(self, current_time = None):
        if self.bot.gw['state'] == False:
            return None
        if current_time is None: current_time = self.bot.getJST()
        if current_time < self.bot.gw['dates']["Preliminaries"] or current_time >= self.bot.gw['dates']["Day 5"]:
            return None
        elif current_time > self.bot.gw['dates']["Day 1"]:
            it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
            for i in range(1, len(it)): # loop to not copy paste this 5 more times
                if current_time > self.bot.gw['dates'][it[i]]:
                    d = self.bot.gw['dates'][it[i-1]] - current_time
                    if d < timedelta(seconds=25200): return None
                    return self.bot.gw['dates'][it[i]] + timedelta(seconds=61200) - current_time
            return None
        elif current_time > self.bot.gw['dates']["Interlude"]:
            return self.bot.gw['dates']["Day 1"] - current_time
        elif current_time > self.bot.gw['dates']["Preliminaries"]:
            return self.bot.gw['dates']["Preliminaries"] + timedelta(seconds=104400) - current_time
        return None

    def isGWRunning(self): # return True if a guild war is on going
        if self.bot.gw['state'] == True:
            current_time = self.bot.getJST()
            if current_time < self.bot.gw['dates']["Preliminaries"]:
                return False
            elif current_time >= self.bot.gw['dates']["End"]:
                self.bot.gw['state'] = False
                self.bot.gw['dates'] = {}
                self.bot.cancelTask('gwtask')
                self.bot.savePending = True
                return False
            else:
                return True
        else:
            return False

    def getNextBuff(self, ctx): # for the (you) crew, get the next set of buffs to be called
        if self.bot.gw['state'] == True and ctx.guild.id == self.bot.ids.get('you_server', 0):
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
                em = self.bot.getEmote(self.bot.gw.get('element', ''))
                if em is None: em = ":white_small_square:"
                title = "{} **Guild War {}** {} Time: **{:%a. %m/%d %H:%M}**\n".format(self.bot.getEmote('gw'), self.bot.gw['id'], em, current_time)
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
                em = self.bot.getEmote(self.bot.gw.get('element', ''))
                if em is None: em = ":white_small_square:"
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {} status".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description=d, color=self.color))
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
                for x in [0, 1]:
                    for c in self.bot.gw['ranking'][x]:
                        if int(c) < 1000:
                            fields[x]['value'] += "**#{:}** \▫️ {:,}".format(c, self.bot.gw['ranking'][x][c])
                        elif int(c) % 1000 != 0:
                            fields[x]['value'] += "**#{:,}.{:,}K** \▫️ {:,}".format(int(c)//1000, (int(c)%1000)//100, self.bot.gw['ranking'][x][c])
                        else:
                            fields[x]['value'] += "**#{:,}K** \▫️ {:,}".format(int(c)//1000, self.bot.gw['ranking'][x][c])
                        if c in self.bot.gw['ranking'][2+x]:
                            if self.bot.gw['ranking'][2+x][c] > 1000000000:
                                fields[x]['value'] += " \▫️  {:,.1f}B/min".format(self.bot.gw['ranking'][2+x][c]/1000000000)
                            elif self.bot.gw['ranking'][2+x][c] > 1000000:
                                fields[x]['value'] += " \▫️  {:,.1f}M/min".format(self.bot.gw['ranking'][2+x][c]/1000000)
                            elif self.bot.gw['ranking'][2+x][c] > 1000:
                                fields[x]['value'] += " \▫️  {:,.1f}K/min".format(self.bot.gw['ranking'][2+x][c]/1000)
                            elif self.bot.gw['ranking'][2+x][c] > 0:
                                fields[x]['value'] += " \▫️  {:,.1f}/min".format(self.bot.gw['ranking'][2+x][c])
                        fields[x]['value'] += "\n"
                    if fields[x]['value'] == '': fields[0]['value'] = 'Unavailable'

                em = self.bot.getEmote(self.bot.gw.get('element', ''))
                if em is None: em = ""
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {}".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), fields=fields, footer="Last Update ▫️ {:%a. %m/%d %H:%M} JST ▫️ Update on minute 5, 25 and 45".format(self.bot.gw['ranking'][4]), inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("ranking", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['estimate', 'estim'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def estimation(self, ctx):
        """Estimate the GW ranking at the end of current day"""
        try:
            if self.bot.gw['state'] == False or self.bot.getJST() < self.bot.gw['dates']["Preliminaries"] or self.bot.gw['ranking'] is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Estimation unavailable", color=self.color))
            else:
                em = self.bot.getEmote(self.bot.gw.get('element', ''))
                if em is None: em = ""
                current_time_left = self.getGWTimeLeft()
                if current_time_left is None:
                    await ctx.send(embed=self.bot.buildEmbed(title="Estimation unavailable", color=self.color))
                    return
                elif current_time_left.days > 0 or current_time_left.seconds > 21900:
                    current_time_left += timedelta(seconds=21900)
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {}".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description="Estimations available in {}".format(self.bot.getTimedeltaStr(current_time_left)), inline=True, color=self.color))
                    return
                time_left = self.getGWTimeLeft(self.bot.gw['ranking'][4])
                time_modifier = (1.1 + 1.2 * (time_left.seconds // 3600) / 10)
                fields = [{'name':'**Crew Ranking**', 'value':''}, {'name':'**Player Ranking**', 'value':''}]
                for x in [0, 1]:
                    for c in self.bot.gw['ranking'][x]:
                        if c in self.bot.gw['ranking'][2+x]:
                            mini = self.bot.gw['ranking'][x][c] + self.bot.gw['ranking'][2+x][c] * time_left.seconds / 60
                            if mini > 1000000000: 
                                mini = mini / 1000000000
                                if mini < 10: mini = "{:,.3f}B".format(mini)
                                else: mini = "{:,.2f}B".format(mini)
                            elif mini > 1000000:
                                mini = mini / 1000000
                                if mini < 10: mini = "{:,.2f}M".format(mini)
                                else: mini = "{:,.1f}M".format(mini)
                            elif mini > 1000:
                                mini = mini / 1000
                                if mini < 10: mini = "{:,.2f}K".format(mini)
                                else: mini = "{:,.1f}K".format(mini)

                            maxi = self.bot.gw['ranking'][x][c] + time_modifier * self.bot.gw['ranking'][2+x][c] * time_left.seconds / 60
                            if maxi > 1000000000: 
                                maxi = maxi / 1000000000
                                if maxi < 10: maxi = "{:,.3f}B".format(maxi)
                                else: maxi = "{:,.2f}B".format(maxi)
                            elif maxi > 1000000:
                                maxi = maxi / 1000000
                                if maxi < 10: maxi = "{:,.2f}M".format(maxi)
                                else: maxi = "{:,.1f}M".format(maxi)
                            elif maxi > 1000:
                                maxi = maxi / 1000
                                if maxi < 10: maxi = "{:,.2f}K".format(maxi)
                                else: maxi = "{:,.1f}K".format(maxi)

                            if int(c) < 1000:
                                fields[x]['value'] += "**#{}** \▫️ {} to {}".format(c, mini, maxi)
                            elif int(c) % 1000 != 0:
                                fields[x]['value'] += "**#{}.{}K** \▫️ {} to {}".format(int(c)//1000, (int(c)%1000)//100, mini, maxi)
                            else:
                                fields[x]['value'] += "**#{}K** \▫️ {} to {}".format(int(c)//1000, mini, maxi)
                            fields[x]['value'] += '\n'
                        
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {}".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description="Time left: **{}**\nThis is a simple estimation, take it with a grain of salt.".format(self.bot.getTimedeltaStr(current_time_left)), fields=fields, footer="Last Update ▫️ {:%a. %m/%d %H:%M} JST ▫️ Update on minute 5, 25 and 45".format(self.bot.gw['ranking'][4]), inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("estimation", str(e))

    async def loadGWDB(self):
        self.loadingdb = True
        try:
            if self.bot.drive.dlFile("GW_old.sql", self.bot.tokens['files']):
                self.conn[0] = sqlite3.connect("GW_old.sql")
                self.cursor[0] = self.conn[0].cursor()
                self.sql[0] = True
            else:
                self.sql[0] = False
        except Exception as e:
            self.sql[0] = None
            await self.bot.sendError('loadGWDB A', str(e))
        try:
            if self.bot.drive.dlFile("GW.sql", self.bot.tokens['files']):
                self.conn[1] = sqlite3.connect("GW.sql")
                self.cursor[1] = self.conn[1].cursor()
                self.sql[1] = True
            else:
                self.sql[1] = False
        except Exception as e:
            self.sql[1] = None
            await self.bot.sendError('loadGWDB B', str(e))
        self.loadingdb = False
        return self.sql

    async def searchGWDBCrew(self, ctx, terms, mode):
        while self.loadingdb: await asyncio.sleep(0.001)
        if self.sql[0] is None or self.sql[1] is None:
            await self.bot.react(ctx, 'time')
            await self.loadGWDB()
            await self.bot.unreact(ctx, 'time')

        data = [None, None]

        for n in range(0, 2):
            if self.sql[n] is not None and self.sql[n] == True:
                data[n] = {}
                try:
                    self.cursor[n].execute("SELECT id FROM GW")
                    for row in self.cursor[n]:
                        data[n]['gw'] = int(row[0])
                        break
                except:
                    pass

                try:
                    if mode == 0:
                        self.cursor[n].execute("SELECT * FROM crews WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 1:
                        self.cursor[n].execute("SELECT * FROM crews WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 2:
                        self.cursor[n].execute("SELECT * FROM crews WHERE id = {}".format(terms))
                    data[n]['result'] = self.cursor[n].fetchall()
                    random.shuffle(data[n]['result'])
                except Exception as e:
                    await self.bot.sendError('searchGWDBCrew {}'.format(n), str(e))
                    data[n] = None

        return data

    async def searchGWDBPlayer(self, ctx, terms, mode):
        while self.loadingdb: await asyncio.sleep(0.001)
        if self.sql[0] is None or self.sql[1] is None:
            await self.bot.react(ctx, 'time')
            await self.loadGWDB()
            await self.bot.unreact(ctx, 'time')

        data = [None, None]

        for n in range(0, 2):
            if self.sql[n] is not None and self.sql[n] == True:
                data[n] = {}
                try:
                    self.cursor[n].execute("SELECT id FROM GW")
                    for row in self.cursor[n]:
                        data[n]['gw'] = int(row[0])
                        break
                except:
                    pass

                try:
                    if mode == 0:
                        self.cursor[n].execute("SELECT * FROM players WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 1:
                        self.cursor[n].execute("SELECT * FROM players WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 2:
                        self.cursor[n].execute("SELECT * FROM players WHERE id = {}".format(terms))
                    data[n]['result'] = self.cursor[n].fetchall()
                    random.shuffle(data[n]['result'])
                except Exception as e:
                    await self.bot.sendError('searchGWDBPlayer {}'.format(n), str(e))
                    data[n] = None

        return data

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def reloadDB(self, ctx):
        """Download GW.sql (Owner only)"""
        while self.loadingdb: await asyncio.sleep(0.001)
        await self.bot.react(ctx, 'time')
        await self.loadGWDB()
        await self.bot.unreact(ctx, 'time')
        if False in self.sql or None in self.sql:
            await ctx.message.add_reaction('❎') # white negative mark
        else:
            await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, hidden=True, aliases=['gwranking'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gbfgranking(self, ctx):
        """Post and sort all /gbfg/ crew per contribution"""
        crews = []
        blacklist = ["677159", "147448"]
        for e in self.bot.granblue['gbfgcrew']:
            if self.bot.granblue['gbfgcrew'][e] in crews or self.bot.granblue['gbfgcrew'][e] in blacklist: continue
            crews.append(self.bot.granblue['gbfgcrew'][e])
        tosort = {}
        possible = {11:"Total Day 4", 9:"Total Day 3", 7:"Total Day 2", 5:"Total Day 1", 3:"Total Prelim."}
        gwid = None
        for c in crews:
            data = await self.searchGWDBCrew(ctx, int(c), 2)
            if data is None or data[1] is None or 'result' not in data[1] or len(data[1]['result']) == 0:
                continue
            result = data[1]['result'][0]
            if gwid is None: gwid = data[1].get('gw', None)
            for ps in possible:
                if result[ps] is not None:
                    if ps == 11 and result[0] is not None:
                        tosort[c] = [c, result[2], int(result[ps]), str(result[0])] # id, name, honor, rank
                        break
                    else:
                        tosort[c] = [c, result[2], int(result[ps]), possible[ps]] # id, name, honor, day
                        break
        sorted = []
        for c in tosort:
            inserted = False
            for i in range(0, len(sorted)):
                if tosort[c][2] > sorted[i][2]:
                    inserted = True
                    sorted.insert(i, tosort[c])
                    break
            if not inserted: sorted.append(tosort[c])
        fields = []
        if gwid is None: gwid = ""
        for i in range(0, len(sorted)):
            if i % 15 == 0: fields.append({'name':'{}'.format(self.bot.getEmote(str(len(fields)+1))), 'value':''})
            if sorted[i][3].startswith('Total'):
                fields[-1]['value'] += "{} \▫️ {} \▫️ **{}**\n".format(i+1, sorted[i][1], self.honor(sorted[i][2]))
            else:
                fields[-1]['value'] += "#**{}** \▫️ {} \▫️ **{}**\n".format(self.honor(sorted[i][3]), sorted[i][1], self.honor(sorted[i][2]))
        await ctx.send(embed=self.bot.buildEmbed(title="{} /gbfg/ GW{} Ranking".format(self.bot.getEmote('gw'), gwid), fields=fields, inline=True, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwcrew'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def findcrew(self, ctx, *, terms : str = ""):
        """Search a crew GW score in the bot data
        add %id to search by id or %eq to get an exact match
        add %all to receive by dm all results (up to 30)
        add %past to get past GW results"""
        if terms == "":
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="**Usage**\n`findcrew [crewname]` to search a crew by name\n`findcrew %eq [crewname]` or `findcrew %== [crewname]` for an exact match\n`findcrew %id [crewid]` for an id search\n`findcrew %all ...` to receive all the results by direct message".format(terms), color=self.color))
            return

        index = terms.find("%all ")
        if index != -1 and index + 5 < len(terms):
            terms = terms.replace("%all ", "")
            all = True
        else:
            all = False

        index = terms.find("%past ")
        if index != -1 and index + 6 < len(terms):
            terms = terms.replace("%past ", "")
            past = True
        else:
            past = False

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
        data = await self.searchGWDBCrew(ctx, terms, mode)
        if data is None:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
            return

        try:
            if data[1] is None or past:
                gwnum = data[0].get('gw', '')
                result = data[0].get('result', [])
            else:
                gwnum = data[1].get('gw', '')
                result = data[1].get('result', [])
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
            return

        if len(result) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` not found".format(terms), footer="help findcrew for details", color=self.color))
            return
        elif all:
            x = len(result)
            if x > 20: x = 20
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Sending your {}/{} result(s)".format(x, len(result)), footer="help findcrew for details", color=self.color))
        elif len(result) > 3: x = 3
        elif len(result) > 1: x = len(result)
        else: x = 1

        fields = []
        for i in range(0, x):
            fields.append({'name':"{}".format(result[i][2]), 'value':''})
            if result[i][0] is not None: fields[-1]['value'] += "▫️**#{}**\n".format(result[i][0])
            else: fields[-1]['value'] += "\n"
            if result[i][3] is not None: fields[-1]['value'] += "**P.** ▫️{:,}\n".format(result[i][3])
            if result[i][4] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('1'), result[i][4])
            if result[i][6] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('2'), result[i][6])
            if result[i][8] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('3'), result[i][8])
            if result[i][10] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('4'), result[i][10])
            if fields[-1]['value'] == "": fields[-1]['value'] = "No data"
            fields[-1]['value'] = "[{}](http://game.granbluefantasy.jp/#guild/detail/{}){}".format(result[i][1], result[i][1], fields[-1]['value'])
            if all:
                try:
                    await ctx.author.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), fields=fields, inline=True, footer="help findcrew for details", color=self.color))
                except:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="I can't send you the full list by private messages", color=self.color))
                    return
                fields = []

        if all:
            await ctx.message.add_reaction('✅') # white check mark
            return
        elif len(result) > 3: desc = "3/{} random result(s) shown".format(len(result))
        else: desc = ""

        await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), description=desc, fields=fields, inline=True, footer="help findcrew for details", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwplayer'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def findplayer(self, ctx, *, terms : str = ""):
        """Search a player GW score in the bot data
        add %id to search by id or %eq to get an exact match
        add %all to receive by dm all results (up to 30)
        add %past to get past GW results"""
        if terms == "":
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="**Usage**\n`findplayer [crewname]` to search a crew by name\n`findplayer %eq [crewname]` or `findplayer %== [crewname]` for an exact match\n`findplayer %id [crewid]` for an id search\n`findplayer %all ...` to receive all the results by direct message".format(terms), color=self.color))
            return

        index = terms.find("%all ")
        if index != -1 and index + 5 < len(terms):
            terms = terms.replace("%all ", "")
            all = True
        else:
            all = False

        index = terms.find("%past ")
        if index != -1 and index + 6 < len(terms):
            terms = terms.replace("%past ", "")
            past = True
        else:
            past = False

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
        data = await self.searchGWDBPlayer(ctx, terms, mode)
        if data is None:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
            return

        try:
            if data[1] is None or past:
                gwnum = data[0].get('gw', '')
                result = data[0].get('result', [])
            else:
                gwnum = data[1].get('gw', '')
                result = data[1].get('result', [])
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
            return

        if len(result) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` not found".format(terms), footer="help findplayer for details", color=self.color))
            return
        elif all:
            x = len(result)
            if x > 30: x = 30
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Sending your {}/{} result(s)".format(x, len(result)), footer="help findplayer for details", color=self.color))
        elif len(result) > 15: x = 15
        elif len(result) > 1: x = len(result)
        else: x = 1
        fields = []
        for i in range(0, x):
            if (not all and (i % 5) == 0) or (all and i == 0):
                fields.append({'name':'Page {}'.format(self.bot.getEmote(str((i // 10) + 1))), 'value':''})
            if result[i][0] is None:
                fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{})\n".format(self.escape(result[i][2]), result[i][1])
            else:
                fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{}) ▫️ **#{}**\n".format(self.escape(result[i][2]), result[i][1], result[i][0])
            if result[i][3] is not None: fields[-1]['value'] += "{:,}\n".format(result[i][3])
            else: fields[-1]['value'] += "n/a\n"
            if all and ((i % 5) == 4 or i == x - 1):
                try:
                    await ctx.author.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), fields=fields, inline=True, footer="help findplayer for details", color=self.color))
                    fields[-1]['value'] = ''
                except:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="I can't send you the full list by private messages", color=self.color))
                    return

        if all:
            await ctx.message.add_reaction('✅') # white check mark
            return
        elif len(result) > 30: desc = "30/{} random result(s) shown".format(len(result))
        else: desc = ""

        await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), description=desc, fields=fields, inline=True, footer="help findplayer for details", color=self.color))