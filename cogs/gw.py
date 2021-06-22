from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import random
import math
from bs4 import BeautifulSoup
from xml.sax import saxutils as su
from urllib.parse import unquote
import threading

# ----------------------------------------------------------------------------------------------------------------
# Guild War Cog
# ----------------------------------------------------------------------------------------------------------------
# Commands related to Unite and Fight and Granblue Fantasy Crews
# ----------------------------------------------------------------------------------------------------------------

class GuildWar(commands.Cog):
    """Unite & Fight and Crew commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xff0000
        self.dbstate = [True, True]
        self.dblock = threading.Lock()
        self.badcrewcache = []
        self.crewcache = {}

    def startTasks(self):
        self.bot.runTask('check_buff', self.checkGWBuff)
        self.bot.runTask('check_ranking', self.bot.ranking.checkgwranking)

    async def checkGWBuff(self): # automatically calls the GW buff used by the (you) crew
        self.getGWState()
        if self.bot.data.save['gw']['state'] == False or len(self.bot.data.save['gw']['buffs']) == 0: return
        try:
            guild = self.bot.get_guild(self.bot.data.config['ids'].get('you_server', 0))
            if guild is None:
                await self.bot.sendError('checkgwbuff', 'cancelled, no guild found')
            channel = self.bot.get_channel(self.bot.data.config['ids'].get('you_announcement', 0))
            gl_role = guild.get_role(self.bot.data.config['ids'].get('gl', 0))
            fo_role = guild.get_role(self.bot.data.config['ids'].get('fo', 0))
            buff_role = [[guild.get_role(self.bot.data.config['ids'].get('atkace', 0)), 'atkace'], [guild.get_role(self.bot.data.config['ids'].get('deface', 0)), 'deface']]
            msg = ""
            while self.bot.data.save['gw']['state'] and (len(self.bot.data.save['gw']['buffs']) > 0 or len(msg) != 0):
                current_time = self.bot.util.JST() + timedelta(seconds=32)
                if len(self.bot.data.save['gw']['buffs']) > 0 and current_time >= self.bot.data.save['gw']['buffs'][0][0]:
                    msg = ""
                    with self.bot.data.lock:
                        if (current_time - self.bot.data.save['gw']['buffs'][0][0]) < timedelta(seconds=200):
                            if self.bot.data.save['gw']['buffs'][0][1]:
                                for r in buff_role:
                                    msg += "{} {}\n".format(self.bot.emote.get(r[1]), r[0].mention)
                            if self.bot.data.save['gw']['buffs'][0][2]:
                                msg += "{} {}\n".format(self.bot.emote.get('foace'), fo_role.mention)
                            if self.bot.data.save['gw']['buffs'][0][4]:
                                if self.bot.data.save['gw']['buffs'][0][3]:
                                    msg += '*Buffs in 5 minutes* **(Use twice this time! They are reset later.)**'
                                else:
                                    msg += 'Buffs now! **(Use twice this time! They are reset later.)**'
                            else:
                                if self.bot.data.save['gw']['buffs'][0][3]:
                                    msg += '*Buffs in 5 minutes*'
                                else:
                                    msg += 'Buffs now!'
                            if self.bot.data.save['gw']['skip']:
                                msg = ""
                            if not self.bot.data.save['gw']['buffs'][0][3]:
                                self.bot.data.save['gw']['skip'] = False
                        self.bot.data.save['gw']['buffs'].pop(0)
                        self.bot.data.pending = True
                else:
                    if msg != "":
                        await channel.send("{} {}\n{}".format(self.bot.emote.get('captain'), gl_role.mention, msg))
                        msg = ""
                    if len(self.bot.data.save['gw']['buffs']) > 0:
                        d = self.bot.data.save['gw']['buffs'][0][0] - current_time
                        if d.seconds > 1:
                            await asyncio.sleep(d.seconds-1)
            if len(msg) > 0:
                await channel.send(msg)
        except asyncio.CancelledError:
            await self.bot.sendError('checkgwbuff', 'cancelled')
        except Exception as e:
            await self.bot.sendError('checkgwbuff', e)
        await self.bot.send('debug', embed=self.bot.util.embed(color=self.color, title="User task ended", description="check_buff", timestamp=self.bot.util.timestamp()))

    def buildDayList(self): # used by the gw schedule command
        return [
            ["{} Automatic BAN Execution".format(self.bot.emote.get('kmr')), "BW", ""],
            ["{} Preliminaries".format(self.bot.emote.get('gold')), "Preliminaries", "Interlude"],
            ["{} Interlude".format(self.bot.emote.get('wood')), "Interlude", "Day 1"],
            ["{} Day 1".format(self.bot.emote.get('1')), "Day 1", "Day 2"],
            ["{} Day 2".format(self.bot.emote.get('2')), "Day 2", "Day 3"],
            ["{} Day 3".format(self.bot.emote.get('3')), "Day 3", "Day 4"],
            ["{} Day 4".format(self.bot.emote.get('4')), "Day 4", "Day 5"],
            ["{} Final Rally".format(self.bot.emote.get('red')), "Day 5", "End"]
        ]

    def isGWRunning(self): # return True if a guild war is on going
        if self.bot.data.save['gw']['state'] == True:
            current_time = self.bot.util.JST()
            if current_time < self.bot.data.save['gw']['dates']["Preliminaries"]:
                return False
            elif current_time >= self.bot.data.save['gw']['dates']["End"]:
                with self.bot.data.lock:
                    self.bot.data.save['gw']['state'] = False
                    self.bot.data.save['gw']['dates'] = {}
                    self.bot.cancelTask('check_buff')
                    self.bot.data.pending = True
                return False
            else:
                return True
        else:
            return False

    def escape(self, s, lite=False): # escape markdown string
        # add the RLO character before
        if lite: return '\u202d' + s.replace('\\', '\\\\').replace('`', '\\`')
        else: return '\u202d' + s.replace('\\', '\\\\').replace('`', '\'').replace('*', '\\*').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('[', '').replace(']', '').replace('(', '\\(').replace(')', '\\)').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('|', '\\|')

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def isYou(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isServer(ctx, 'you_server')
        return commands.check(predicate)

    def isYouModOrOwner(): # for decorators
        async def predicate(ctx):
            return (ctx.bot.isServer(ctx, 'debug_server') or (ctx.bot.isServer(ctx, 'you_server') and ctx.bot.isMod(ctx)))
        return commands.check(predicate)

    def honorFormat(self, h): # convert honor number to a shorter string version
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
        if self.bot.data.save['gw']['state'] == True:
            current_time = self.bot.util.JST()
            if current_time < self.bot.data.save['gw']['dates']["Preliminaries"]:
                d = self.bot.data.save['gw']['dates']["Preliminaries"] - current_time
                return "{} Guild War starts in **{}**".format(self.bot.emote.get('gw'), self.bot.util.delta2str(d, 2))
            elif current_time >= self.bot.data.save['gw']['dates']["End"]:
                with self.bot.data.lock:
                    self.bot.data.save['gw']['state'] = False
                    self.bot.data.save['gw']['dates'] = {}
                    self.bot.cancelTask('check_buff')
                    self.bot.data.save['youtracker'] = None
                    self.bot.data.pending = True
                return ""
            elif current_time > self.bot.data.save['gw']['dates']["Day 5"]:
                d = self.bot.data.save['gw']['dates']["End"] - current_time
                return "{} Final Rally is on going\n{} Guild War ends in **{}**".format(self.bot.emote.get('mark_a'), self.bot.emote.get('time'), self.bot.util.delta2str(d))
            elif current_time > self.bot.data.save['gw']['dates']["Day 1"]:
                it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
                for i in range(1, len(it)): # loop to not copy paste this 5 more times
                    if current_time > self.bot.data.save['gw']['dates'][it[i]]:
                        d = self.bot.data.save['gw']['dates'][it[i-1]] - current_time
                        if d < timedelta(seconds=25200): msg = "{} {} ended".format(self.bot.emote.get('mark_a'), it[i])
                        else: msg = "{} GW {} is on going (Time left: **{}**)".format(self.bot.emote.get('mark_a'), it[i], self.bot.util.delta2str(self.bot.data.save['gw']['dates'][it[i]] + timedelta(seconds=61200) - current_time))
                        if i == 1: return "{}\n{} {} starts in **{}**".format(msg, self.bot.emote.get('time'), it[i-1].replace('Day 5', 'Final Rally'), self.bot.util.delta2str(d))
                        else: return "{}\n{} {} starts in **{}**".format(msg, self.bot.emote.get('time'), it[i-1], self.bot.util.delta2str(d))
            elif current_time > self.bot.data.save['gw']['dates']["Interlude"]:
                d = self.bot.data.save['gw']['dates']["Day 1"] - current_time
                return "{} Interlude is on going\n{} Day 1 starts in **{}**".format(self.bot.emote.get('mark_a'), self.bot.emote.get('time'), self.bot.util.delta2str(d))
            elif current_time > self.bot.data.save['gw']['dates']["Preliminaries"]:
                d = self.bot.data.save['gw']['dates']['Interlude'] - current_time
                if d < timedelta(seconds=25200): msg = "{} Preliminaries ended".format(self.bot.emote.get('mark_a'))
                else: msg = "{} Preliminaries are on going (Time left: **{}**)".format(self.bot.emote.get('mark_a'), self.bot.util.delta2str(self.bot.data.save['gw']['dates']["Preliminaries"] + timedelta(seconds=104400) - current_time, 2))
                return "{}\n{} Interlude starts in **{}**".format(msg, self.bot.emote.get('time'), self.bot.util.delta2str(d, 2))
            else:
                return ""
        else:
            return ""

    def formatElement(self, elem):
        return "{}⚔️{}".format(self.bot.emote.get(elem), self.bot.emote.get({'fire':'wind', 'water':'fire', 'earth':'water', 'wind':'earth', 'light':'dark', 'dark':'light'}.get(elem)))
        
    def getGWTimeLeft(self, current_time = None):
        if self.bot.data.save['gw']['state'] == False:
            return None
        if current_time is None: current_time = self.bot.util.JST()
        if current_time < self.bot.data.save['gw']['dates']["Preliminaries"] or current_time >= self.bot.data.save['gw']['dates']["Day 5"]:
            return None
        elif current_time > self.bot.data.save['gw']['dates']["Day 1"]:
            it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
            for i in range(1, len(it)): # loop to not copy paste this 5 more times
                if current_time > self.bot.data.save['gw']['dates'][it[i]]:
                    if self.bot.data.save['gw']['dates'][it[i-1]] - current_time < timedelta(seconds=25200): return None
                    return self.bot.data.save['gw']['dates'][it[i]] + timedelta(seconds=61200) - current_time
            return None
        elif current_time > self.bot.data.save['gw']['dates']["Interlude"]:
            return self.bot.data.save['gw']['dates']["Day 1"] - current_time
        elif current_time > self.bot.data.save['gw']['dates']["Preliminaries"]:
            if self.bot.data.save['gw']['dates']["Interlude"] - current_time < timedelta(seconds=25200): return None
            return self.bot.data.save['gw']['dates']["Preliminaries"] + timedelta(seconds=104400) - current_time
        return None

    def getNextBuff(self, ctx): # for the (you) crew, get the next set of buffs to be called
        if self.bot.data.save['gw']['state'] == True and ctx.guild.id == self.bot.data.config['ids'].get('you_server', 0):
            current_time = self.bot.util.JST()
            if current_time < self.bot.data.save['gw']['dates']["Preliminaries"]:
                return ""
            for b in self.bot.data.save['gw']['buffs']:
                if not b[3] and current_time < b[0]:
                    msg = "{} Next buffs in **{}** (".format(self.bot.emote.get('question'), self.bot.util.delta2str(b[0] - current_time, 2))
                    if b[1]:
                        msg += "Attack {}, Defense {}".format(self.bot.emote.get('atkace'), self.bot.emote.get('deface'))
                        if b[2]:
                            msg += ", FO {}".format(self.bot.emote.get('foace'))
                    elif b[2]:
                        msg += "FO {}".format(self.bot.emote.get('foace'))
                    msg += ")"
                    return msg
        return ""

    @commands.command(no_pm=True)
    @isOwner()
    async def newgwtask(self, ctx):
        """Start a new checkGWBuff() task (Owner Only)"""
        self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def GW(self, ctx, gmt : int = 9):
        """Post the GW schedule"""
        if self.bot.data.save['gw']['state'] == True:
            try:
                if gmt < -12 or gmt > 14: gmt = 9
                current_time = self.bot.util.JST()
                em = self.formatElement(self.bot.data.save['gw']['element'])
                title = "{} **Guild War {}** {} **{:%a. %m/%d %H:%M} TZ**\n".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em, current_time + timedelta(seconds=3600*(gmt-9)))
                if gmt == 9: title = title.replace('TZ', 'JST')
                elif gmt == 0: title = title.replace('TZ', 'GMT')
                else: title = title.replace('TZ', 'GMT{0:+}'.format(gmt))
                description = ""
                day_list = self.buildDayList()
                if current_time < self.bot.data.save['gw']['dates']["End"]:
                    for it in day_list:
                        if it[1] == "BW":
                            d = self.bot.data.save['gw']['dates']["Preliminaries"] - timedelta(days=random.randint(1, 4)) + timedelta(seconds=3600*(gmt-9))
                            if current_time < d and random.randint(1, 8) == 1:
                                description += it[0] + " **{:%a. %m/%d %H:%M}**\n".format(d)
                        else:
                            if self.dayCheck(current_time, self.bot.data.save['gw']['dates'][it[2]], it[1]=="Day 5") or (it[1] == "Interlude" and self.dayCheck(current_time, self.bot.data.save['gw']['dates'][it[2]] + timedelta(seconds=25200), False)):
                                description += it[0] + ": **{:%a. %m/%d %H:%M}**\n".format(self.bot.data.save['gw']['dates'][it[1]] + timedelta(seconds=3600*(gmt-9)))
                else:
                    await ctx.send(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Not available", color=self.color))
                    with self.bot.data.lock:
                        self.bot.data.save['gw']['state'] = False
                        self.bot.data.save['gw']['dates'] = {}
                        self.bot.cancelTask('check_buff')
                        self.bot.data.save['youtracker'] = None
                        self.bot.data.pending = True
                    return

                try:
                    description += self.getGWState()
                except Exception as e:
                    await self.bot.sendError("getgwstate", e)

                try:
                    description += '\n' + self.getNextBuff(ctx)
                except Exception as e:
                    await self.bot.sendError("getnextbuff", e)

                await ctx.send(embed=self.bot.util.embed(title=title, description=description, color=self.color))
            except Exception as e:
                await self.bot.sendError("gw", e)
        else:
            await ctx.send(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Not available", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwtime'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def fugdidgwstart(self, ctx):
        """Check if GW started"""
        try:
            d = self.getGWState()
            if d != "":
                em = self.formatElement(self.bot.data.save['gw']['element'])
                await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War {}** {} status".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description=d, color=self.color))
        except Exception as e:
            await ctx.reply(embed=self.bot.util.embed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("fugdidgwstart", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['buff'])
    @isYou()
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def GWbuff(self, ctx):
        """Check when is the next GW buff
        (You) Server Only"""
        try:
            d = self.getNextBuff(ctx)
            if d != "":
                await ctx.reply(embed=self.bot.util.embed(title="{} Guild War (You) Buff status".format(self.bot.emote.get('gw')), description=d, color=self.color))
            else:
                await ctx.reply(embed=self.bot.util.embed(title="{} Guild War (You) Buff status".format(self.bot.emote.get('gw')), description="Only available when Guild War is on going", color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("gwbuff", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rankings', 'cutoff', 'cutoffs'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def ranking(self, ctx):
        """Retrieve the current GW ranking"""
        try:
            if self.bot.data.save['gw']['state'] == False or self.bot.util.JST() < self.bot.data.save['gw']['dates']["Preliminaries"] or self.bot.data.save['gw']['ranking'] is None:
                await ctx.send(embed=self.bot.util.embed(title="Ranking unavailable", color=self.color))
            else:
                fields = [{'name':'**Crew Ranking**', 'value':''}, {'name':'**Player Ranking**', 'value':''}]
                for x in [0, 1]:
                    for c in self.bot.data.save['gw']['ranking'][x]:
                        if int(c) < 1000:
                            fields[x]['value'] += "**#{:}** \▫️ {:,}".format(c, self.bot.data.save['gw']['ranking'][x][c])
                        elif int(c) % 1000 != 0:
                            fields[x]['value'] += "**#{:,}.{:,}K** \▫️ {:,}".format(int(c)//1000, (int(c)%1000)//100, self.bot.data.save['gw']['ranking'][x][c])
                        else:
                            fields[x]['value'] += "**#{:,}K** \▫️ {:,}".format(int(c)//1000, self.bot.data.save['gw']['ranking'][x][c])
                        if c in self.bot.data.save['gw']['ranking'][2+x]:
                            if self.bot.data.save['gw']['ranking'][2+x][c] > 1000000000:
                                fields[x]['value'] += " \▫️  {:,.1f}B/min".format(self.bot.data.save['gw']['ranking'][2+x][c]/1000000000)
                            elif self.bot.data.save['gw']['ranking'][2+x][c] > 1000000:
                                fields[x]['value'] += " \▫️  {:,.1f}M/min".format(self.bot.data.save['gw']['ranking'][2+x][c]/1000000)
                            elif self.bot.data.save['gw']['ranking'][2+x][c] > 1000:
                                fields[x]['value'] += " \▫️  {:,.1f}K/min".format(self.bot.data.save['gw']['ranking'][2+x][c]/1000)
                            elif self.bot.data.save['gw']['ranking'][2+x][c] > 0:
                                fields[x]['value'] += " \▫️  {:,.1f}/min".format(self.bot.data.save['gw']['ranking'][2+x][c])
                        fields[x]['value'] += "\n"
                    if fields[x]['value'] == '': fields[0]['value'] = 'Unavailable'

                em = self.formatElement(self.bot.data.save['gw']['element'])
                d = self.bot.util.JST() - self.bot.data.save['gw']['ranking'][4]
                await ctx.send(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Updated: **{}** ago".format(self.bot.util.delta2str(d, 0)), fields=fields, footer="Update on minute 5, 25 and 45", inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("ranking", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['estimate', 'estimates', 'estim', 'predict', 'prediction', 'predictions'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def estimation(self, ctx):
        """Estimate the GW ranking at the end of current day"""
        try:
            if self.bot.data.save['gw']['state'] == False or self.bot.util.JST() < self.bot.data.save['gw']['dates']["Preliminaries"] or self.bot.data.save['gw']['ranking'] is None:
                await ctx.send(embed=self.bot.util.embed(title="Estimation unavailable", color=self.color))
            else:
                em = self.formatElement(self.bot.data.save['gw']['element'])
                current_time_left = self.getGWTimeLeft()
                if current_time_left is None:
                    await ctx.send(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Estimations are currently unavailable", inline=True, color=self.color))
                    return
                elif current_time_left.days > 0 or current_time_left.seconds > 21300:
                    current_time_left -= timedelta(seconds=21300)
                    await ctx.send(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Estimations available in **{}**".format(self.bot.util.delta2str(current_time_left)), inline=True, color=self.color))
                    return
                time_left = self.getGWTimeLeft(self.bot.data.save['gw']['ranking'][4])
                fields = [{'name':'**Crew Ranking**', 'value':''}, {'name':'**Player Ranking**', 'value':''}]
                for x in [0, 1]:
                    for c in self.bot.data.save['gw']['ranking'][x]:
                        if c in self.bot.data.save['gw']['ranking'][2+x] and self.bot.data.save['gw']['ranking'][2+x][c] > 0:
                            predi = [0, 0]
                            for y in [0, 1]:
                                if y == 0: predi[y] = self.bot.data.save['gw']['ranking'][x][c] + (1 + 1.5 * (time_left.seconds // 7200) / 10) + self.bot.data.save['gw']['ranking'][2+x][c] * time_left.seconds / 60 # minimum
                                elif y == 1:  predi[y] = self.bot.data.save['gw']['ranking'][x][c] + (1.1 + 1.3 * (time_left.seconds // 3600) / 10) * self.bot.data.save['gw']['ranking'][2+x][c] * time_left.seconds / 60 # maximum
                                # formatting
                                if predi[y] > 1000000000: 
                                    predi[y] = predi[y] / 1000000000
                                    if predi[y] < 10: predi[y] = "{:,.3f}B".format(predi[y])
                                    else: predi[y] = "{:,.2f}B".format(predi[y])
                                elif predi[y] > 1000000:
                                    predi[y] = predi[y] / 1000000
                                    if predi[y] < 10: predi[y] = "{:,.2f}M".format(predi[y])
                                    else: predi[y] = "{:,.1f}M".format(predi[y])
                                elif predi[y] > 1000:
                                    predi[y] = predi[y] / 1000
                                    if predi[y] < 10: predi[y] = "{:,.2f}K".format(predi[y])
                                    else: predi[y] = "{:,.1f}K".format(predi[y])

                            # display
                            if predi[0] == predi[1]: # if min and max equal
                                if int(c) < 1000:
                                    fields[x]['value'] += "**#{}** \▫️ {}".format(c, predi[0])
                                elif int(c) % 1000 != 0:
                                    fields[x]['value'] += "**#{}.{}K** \▫️ {}".format(int(c)//1000, (int(c)%1000)//100, predi[0])
                                else:
                                    fields[x]['value'] += "**#{}K** \▫️ {}".format(int(c)//1000, predi[0])
                            else:
                                if int(c) < 1000:
                                    fields[x]['value'] += "**#{}** \▫️ {} to {}".format(c, predi[0], predi[1])
                                elif int(c) % 1000 != 0:
                                    fields[x]['value'] += "**#{}.{}K** \▫️ {} to {}".format(int(c)//1000, (int(c)%1000)//100, predi[0], predi[1])
                                else:
                                    fields[x]['value'] += "**#{}K** \▫️ {} to {}".format(int(c)//1000, predi[0], predi[1])
                            fields[x]['value'] += '\n'
                        else:
                            if int(c) < 1000:
                                fields[x]['value'] += "**#{}** \▫️ Unavailable".format(c)
                            elif int(c) % 1000 != 0:
                                fields[x]['value'] += "**#{}.{}K** \▫️ Unavailable".format(int(c)//1000, (int(c)%1000)//100)
                            else:
                                fields[x]['value'] += "**#{}K** \▫️ Unavailable".format(int(c)//1000)
                            fields[x]['value'] += '\n'
                    if fields[x]['value'] == '': fields[x]['value'] = 'Unavailable'
                d = self.bot.util.JST() - self.bot.data.save['gw']['ranking'][4]
                await ctx.send(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Time left: **{}** \▫️ Updated: **{}** ago\nThis is a simple estimation, take it with a grain of salt.".format(self.bot.util.delta2str(current_time_left), self.bot.util.delta2str(d, 0)), fields=fields, footer="Update on minute 5, 25 and 45", timestamp=self.bot.util.timestamp(), inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("estimation", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isYouModOrOwner()
    async def setGW(self, ctx, id : int, advElement : str, day : int, month : int, year : int):
        """Set the GW date ((You) Mod Only)"""
        try:
            # stop the task
            self.bot.cancelTask('check_buff')
            with self.bot.data.lock:
                self.bot.data.save['gw']['state'] = False
                self.bot.data.save['gw']['id'] = id
                self.bot.data.save['gw']['ranking'] = ""
                self.bot.data.save['gw']['element'] = advElement.lower()
                # build the calendar
                self.bot.data.save['gw']['dates'] = {}
                self.bot.data.save['gw']['dates']["Preliminaries"] = datetime.utcnow().replace(year=year, month=month, day=day, hour=19, minute=0, second=0, microsecond=0)
                self.bot.data.save['gw']['dates']["Interlude"] = self.bot.data.save['gw']['dates']["Preliminaries"] + timedelta(days=1, seconds=43200) # +36h
                self.bot.data.save['gw']['dates']["Day 1"] = self.bot.data.save['gw']['dates']["Interlude"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 2"] = self.bot.data.save['gw']['dates']["Day 1"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 3"] = self.bot.data.save['gw']['dates']["Day 2"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 4"] = self.bot.data.save['gw']['dates']["Day 3"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 5"] = self.bot.data.save['gw']['dates']["Day 4"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["End"] = self.bot.data.save['gw']['dates']["Day 5"] + timedelta(seconds=61200) # +17h
                # build the buff list for (you)
                self.bot.data.save['gw']['buffs'] = []
                # Prelims all
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=7200-300), True, True, True, True]) # warning, double
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=7200), True, True, False, True])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200-300), True, False, True, False]) # warning
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200), True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200+3600-300), False, True, True, False]) # warning
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200+3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(days=1, seconds=10800-300), True, True, True, False]) # warning
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(days=1, seconds=10800), True, True, False, False])
                # Interlude
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=54000), True, True, False, False])
                # Day 1
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=54000), True, True, False, False])
                # Day 2
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=54000), True, True, False, False])
                # Day 3
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=54000), True, True, False, False])
                # Day 4
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=54000), True, True, False, False])
                # set the gw state to true
                self.bot.data.save['gw']['state'] = True
                self.bot.data.pending = True
            self.bot.runTask('check_buff', self.checkGWBuff)
            await ctx.send(embed=self.bot.util.embed(title="{} Guild War Mode".format(self.bot.emote.get('gw')), description="Set to : **{:%m/%d %H:%M}**".format(self.bot.data.save['gw']['dates']["Preliminaries"]), color=self.color))
        except Exception as e:
            self.bot.cancelTask('check_buff')
            with self.bot.data.lock:
                self.bot.data.save['gw']['dates'] = {}
                self.bot.data.save['gw']['buffs'] = []
                self.bot.data.save['gw']['state'] = False
                self.bot.data.pending = True
            await ctx.send(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", footer=str(e), color=self.color))
            await self.bot.sendError('setgw', e)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isYouModOrOwner()
    async def disableGW(self, ctx):
        """Disable the GW mode ((You) Mod Only)
        It doesn't delete the GW settings"""
        self.bot.cancelTask('check_buff')
        with self.bot.data.lock:
            self.bot.data.save['gw']['state'] = False
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isYouModOrOwner()
    async def enableGW(self, ctx):
        """Enable the GW mode ((You) Mod Only)"""
        if self.bot.data.save['gw']['state'] == True:
            await ctx.send(embed=self.bot.util.embed(title="{} Guild War Mode".format(self.bot.emote.get('gw')), description="Already enabled", color=self.color))
        elif len(self.bot.data.save['gw']['dates']) == 8:
            with self.bot.data.lock:
                self.bot.data.save['gw']['state'] = True
                self.bot.data.pending = True
            self.bot.runTask('check_buff', self.checkGWBuff)
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="No Guild War available in my memory", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['skipGW'])
    @isYouModOrOwner()
    async def skipGWBuff(self, ctx):
        """The bot will skip the next GW buff call ((You) Mod Only)"""
        if not self.bot.data.save['gw']['skip']:
            with self.bot.data.lock:
                self.bot.data.save['gw']['skip'] = True
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="I'm already skipping the next set of buffs", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isYouModOrOwner()
    async def cancelSkipGWBuff(self, ctx):
        """Cancel the GW buff call skipping ((You) Mod Only)"""
        if self.bot.data.save['gw']['skip']:
            with self.bot.data.lock:
                self.bot.data.save['gw']['skip'] = False
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="No buff skip is currently set", color=self.color))

    def loadGWDB(self, ids = [0, 1]):
        fs = ["GW_old.sql", "GW.sql"]
        for i in ids:
            try:
                self.dbstate[i] = False
                self.bot.sql.remove(fs[i])
                if self.bot.drive.dlFile(fs[i], self.bot.data.config['tokens']['files']):
                    self.bot.sql.add(fs[i])
                    self.dbstate[i] = True
            except:
                print("Failed to load database", fs[i])
                self.bot.errn += 1

    def reloadGWDB(self):
        with self.dblock:
            self.dbstate = [True, True]
            self.loadGWDB()

    def GWDBver(self):
        fs = ["GW_old.sql", "GW.sql"]
        res = [None, None]
        for i in [0, 1]:
            with self.dblock:
                db = self.bot.sql.get(fs[i])
                if db is None:
                    if not self.dbstate[i]: continue
                    self.loadGWDB([i])
                    db = self.bot.sql.get(fs[i])
                    if db is None:
                        continue
            c = db.open()
            if c is None: continue
            try:
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'")
                if c.fetchone()[0] < 1:
                    c.execute("SELECT * FROM GW")
                    for row in c.fetchall():
                        res[i] = {'gw':int(row[0]), 'ver':1}
                        break
                else:
                    c.execute("SELECT * FROM info")
                    for row in c.fetchall():
                        res[i] = {'gw':int(row[0]), 'ver':int(row[1])}
                        break
            except:
                res[i] = {'ver':0}
            db.close()
        return res

    def searchGWDB(self, terms, mode):
        data = self.GWDBver()
        dbs = [self.bot.sql.get("GW_old.sql"), self.bot.sql.get("GW.sql")]
        cs = []
        for n in [0, 1]:
            cs.append(dbs[n].open())

        for n in [0, 1]:
            if cs[n] is not None and data[n] is not None:
                try:
                    c = cs[n]
                    if mode == 10:
                        c.execute("SELECT * FROM crews WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 11:
                        c.execute("SELECT * FROM crews WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 12:
                        c.execute("SELECT * FROM crews WHERE id = {}".format(terms))
                    elif mode == 13:
                        c.execute("SELECT * FROM crews WHERE ranking = {}".format(terms))
                    elif mode == 0:
                        c.execute("SELECT * FROM players WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 1:
                        c.execute("SELECT * FROM players WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 2:
                        c.execute("SELECT * FROM players WHERE id = {}".format(terms))
                    elif mode == 3:
                        c.execute("SELECT * FROM players WHERE ranking = {}".format(terms))
                    data[n]['result'] = c.fetchall()
                    random.shuffle(data[n]['result'])
                except Exception as e:
                    print('searchGWDB', n, 'mode', mode, ':', self.bot.util.pexc(e))
                    self.bot.errn += 1
                    data[n] = None
                dbs[n].close()
        return data

    def searchGWDBCrew(self, terms, mode):
        return self.searchGWDB(terms, mode+10)

    def searchGWDBPlayer(self, terms, mode):
        return self.searchGWDB(terms, mode)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def reloadDB(self, ctx):
        """Download GW.sql (Owner Only)"""
        await self.bot.util.react(ctx.message, 'time')
        await self.bot.do(self.reloadGWDB)
        vers = await self.bot.do(self.GWDBver)
        await self.bot.util.unreact(ctx.message, 'time')
        msg = ""
        for i in [0, 1]:
            msg += "**{}** :white_small_square: ".format('GW_old.sql' if (i == 0) else 'GW.sql')
            if vers[i] is None: msg += "Not loaded"
            else:
                msg += 'GW{} '.format(vers[i].get('gw', '??'))
                msg += '(version {})'.format(vers[i].get('ver', 'ERROR'))
            msg += "\n"
        await self.bot.send('debug', embed=self.bot.util.embed(title="Guild War Databases", description=msg, timestamp=self.bot.util.timestamp(), color=self.color))

    async def findranking(self, ctx, type, terms): # it's a mess, I won't comment it
        if type: txt = "crew"
        else: txt = "player"
        if terms == "":
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="**Usage**\n`find{} [crewname]` to search a {} by name\n`find{} %eq [{}name]` or `find{} %== [{}name]` for an exact match\n`find{} %id [{}id]` for an id search\n`find{} %rank [ranking]` for a ranking search\n`find{} %all ...` to receive all the results by direct message".format(txt, txt, txt, txt, txt, txt, txt, txt, txt, txt), color=self.color))
        else:
            try:
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
                        final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                elif terms.startswith("%rank "):
                    try:
                        terms = int(terms[6:])
                        mode = 3
                    except:
                        final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                else:
                    mode = 0
                if type: data = await self.bot.do(self.searchGWDBCrew, terms, mode)
                else: data = await self.bot.do(self.searchGWDBPlayer, terms, mode)
                if data is None:
                    final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Database unavailable", color=self.color))
                    raise Exception("Returning")

                try:
                    if data[1] is None or past:
                        gwnum = data[0].get('gw', '')
                        ver = data[0].get('ver', '')
                        result = data[0].get('result', [])
                    else:
                        gwnum = data[1].get('gw', '')
                        ver = data[1].get('ver', '')
                        result = data[1].get('result', [])
                except:
                    final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Database unavailable", color=self.color))
                    raise Exception("Returning")

                if len(result) == 0:
                    final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="`{}` not found".format(terms), footer="help find{} for details".format(txt), color=self.color))
                    raise Exception("Returning")
                elif all:
                    if type: xl = 36
                    else: xl = 80
                    x = len(result)
                    if x > xl: x = xl
                    final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Sending your {}/{} result(s)".format(x, len(result)), footer="help find{} for details".format(txt), color=self.color))
                elif type and len(result) > 6: x = 6 # crew
                elif not type and len(result) > 15: x = 15 # player
                elif len(result) > 1: x = len(result)
                else: x = 1
                fields = []
                for i in range(0, x):
                    if type: # crew -----------------------------------------------------------------
                        fields.append({'name':"{}".format(result[i][2]), 'value':''})
                        if result[i][0] is not None: fields[-1]['value'] += "▫️**#{}**\n".format(result[i][0])
                        else: fields[-1]['value'] += "\n"
                        if result[i][3] is not None: fields[-1]['value'] += "**P.** ▫️{:,}\n".format(result[i][3])
                        if ver == 2:
                            if result[i][4] is not None and result[i][3] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('1'), result[i][4]-result[i][3])
                            if result[i][5] is not None and result[i][4] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('1'), result[i][5]-result[i][4])
                            if result[i][6] is not None and result[i][5] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('1'), result[i][6]-result[i][5])
                            if result[i][7] is not None and result[i][6] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('1'), result[i][7]-result[i][6])
                        else:
                            if result[i][4] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('1'), result[i][4])
                            if result[i][6] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('2'), result[i][6])
                            if result[i][8] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('3'), result[i][8])
                            if result[i][10] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('4'), result[i][10])
                        if fields[-1]['value'] == "": fields[-1]['value'] = "No data"
                        fields[-1]['value'] = "[{}](http://game.granbluefantasy.jp/#guild/detail/{}){}".format(result[i][1], result[i][1], fields[-1]['value'])
                        if all and ((i % 6) == 5 or i == x - 1):
                            try:
                                await ctx.author.send(embed=self.bot.util.embed(title="{} **Guild War {}**".format(self.bot.emote.get('gw'), gwnum), fields=fields, inline=True, footer="help findcrew for details", color=self.color))
                            except:
                                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="I can't send you the full list by private messages", color=self.color))
                                raise Exception("Returning")
                            fields = []
                    else: # player -----------------------------------------------------------------
                        if i % 5 == 0:
                            fields.append({'name':'Page {}'.format(self.bot.emote.get(str(((i // 5) % 3) + 1))), 'value':''})
                        if result[i][0] is None:
                            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{})\n".format(self.escape(result[i][2]), result[i][1])
                        else:
                            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{}) ▫️ **#{}**\n".format(self.escape(result[i][2]), result[i][1], result[i][0])
                        if result[i][3] is not None: fields[-1]['value'] += "{:,}\n".format(result[i][3])
                        else: fields[-1]['value'] += "n/a\n"
                        if all and ((i % 15) == 14 or i == x - 1):
                            try:
                                await ctx.author.send(embed=self.bot.util.embed(title="{} **Guild War {}**".format(self.bot.emote.get('gw'), gwnum), fields=fields, inline=True, footer="help findplayer for details", color=self.color))
                            except:
                                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="I can't send you the full list by private messages", color=self.color))
                                raise Exception("Returning")
                            fields = []

                if all:
                    await self.bot.util.react(ctx.message, '✅') # white check mark
                    raise Exception("Returning")
                elif type and len(result) > 6: desc = "6/{} random result(s) shown".format(len(result)) # crew
                elif not type and len(result) > 30: desc = "30/{} random result(s) shown".format(len(result)) # player
                else: desc = ""
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War {}**".format(self.bot.emote.get('gw'), gwnum), description=desc, fields=fields, inline=True, footer="help find{} for details".format(txt), color=self.color))
            except Exception as e:
                print(self.bot.util.pexc(e))
        await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwcrew'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def findcrew(self, ctx, *, terms : str = ""):
        """Search a crew GW score in the bot data
        add %id to search by id or %eq to get an exact match
        add %all to receive by dm all results (up to 30)
        add %past to get past GW results"""
        await self.findranking(ctx, True, terms)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwplayer'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def findplayer(self, ctx, *, terms : str = ""):
        """Search a player GW score in the bot data
        add %id to search by id or %eq to get an exact match
        add %all to receive by dm all results (up to 30)
        add %past to get past GW results"""
        await self.findranking(ctx, False, terms)

    def strToInt(self, s): # convert string such as 1.2B to 1200000000
        try:
            return int(s)
        except:
            n = float(s[:-1]) # float to support for example 1.2B
            m = s[-1].lower()
            l = {'k':1000, 'm':1000000, 'b':1000000000}
            return int(n * l[m])

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tokens', 'gwtoken', 'guildwartoken', 'gwtokens', 'guildwartokens'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def token(self, ctx, tok : str):
        """Calculate how many Guild War boxes you get from X tokens"""
        try:
            tok = self.strToInt(tok)
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
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} Guild War Token Calculator ▫️ {} tokens".format(self.bot.emote.get('gw'), t), description="**{:,}** box(s) and **{:,}** leftover tokens\n**{:,}** EX (**{:,}** pots)\n**{:,}** EX+ (**{:,}** pots)\n**{:,}** NM90 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM95 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM150 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 join (**{:}** BP)".format(b, tok, ex, math.ceil(ex*30/75), explus, math.ceil(explus*30/75), n90, math.ceil(n90*30/75), n90*5, n95, math.ceil(n95*40/75), n95*10, n100, math.ceil(n100*50/75), n100*20, n150, math.ceil(n150*50/75), n150*20, wanpan, wanpan*3), color=self.color))
        except:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Error", description="Invalid token number", color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwbox', 'guildwarbox'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def box(self, ctx, box : int):
        """Calculate how many Guild War tokens you need"""
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
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} Guild War Token Calculator ▫️ {} boxes".format(self.bot.emote.get('gw'), b), description="**{:,}** tokens needed\n\n**{:,}** EX (**{:,}** pots)\n**{:,}** EX+ (**{:,}** pots)\n**{:,}** NM90 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM95 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM150 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 join (**{:}** BP)".format(t, ex, math.ceil(ex*30/75), explus, math.ceil(explus*30/75), n90, math.ceil(n90*30/75), n90*5, n95, math.ceil(n95*40/75), n95*10, n100, math.ceil(n100*50/75), n100*20, n150, math.ceil(n150*50/75), n150*20, wanpan, wanpan*3), color=self.color))
        except:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Error", description="Invalid box number", color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def meat(self, ctx, meat : str):
        """Calculate how many Guild War honors you get"""
        try:
            meat = self.strToInt(meat)
            if meat < 5 or meat > 100000: raise Exception()
            nm90 = meat // 5
            nm95 = meat // 10
            nm100 = meat // 20
            nm150 = meat // 20
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} Meat Calculator ▫️ {} meats".format(self.bot.emote.get('gw'), meat), description="**{:,}** NM90 or **{:}** honors\n**{:,}** NM95 or **{:}** honors\n**{:}** NM100 or **{:}** honors\n**{:,}** NM150 or **{:}** honors\n".format(nm90, self.honorFormat(nm90*260000), nm95, self.honorFormat(nm95*910000), nm100, self.honorFormat(nm100*2650000), nm150, self.honorFormat(nm150*4100000)), color=self.color))
        except:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Error", description="Invalid meat number", color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['honors'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def honor(self, ctx, target : str):
        """Calculate how many NM95 and 150 you need for your targeted honor"""
        try:
            target = self.strToInt(target)
            if target < 10000: raise Exception()
            honor = [0, 0, 0]
            ex = 0
            meat_per_ex_average = 4
            meat = 0
            total_meat = 0
            nm = [0, 0]
            day_target = [target * 0.2, target * 0.3] # sum = 0.5
            meat_use = [10, 20]
            honor_per_nm = [910000, 4100000]

            for i in [1, 0]:
                daily = 0
                while daily < day_target[i]:
                    if meat < meat_use[i]:
                        meat += meat_per_ex_average
                        total_meat += meat_per_ex_average
                        ex += 1
                        daily += 80800
                        honor[0] += 80800
                    else:
                        meat -= meat_use[i]
                        nm[i] += 1
                        daily += honor_per_nm[i]
                        honor[i+1] += honor_per_nm[i]

            final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} Honor Planning ▫️ {} honors".format(self.bot.emote.get('gw'), self.honorFormat(target)), description="Preliminaries & Interlude ▫️ **{:,}** meats (around **{:,}** EX+ and **{:}** honors)\nDay 1 and 2 total ▫️ **{:,}** NM95 (**{:}** honors)\nDay 3 and 4 total ▫️ **{:,}** NM150 (**{:}** honors)".format(math.ceil(total_meat*2), ex*2, self.honorFormat(honor[0]*2), nm[0]*2, self.honorFormat(honor[1]*2), nm[1]*2, self.honorFormat(honor[2]*2)), footer="Assuming {} meats / EX+ on average".format(meat_per_ex_average), color=self.color))
        except:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Error", description="Invalid honor number", color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    def getCrewSummary(self, id):
        res = self.bot.gbf.request("http://game.granbluefantasy.jp/guild_main/content/detail/{}?PARAMS".format(id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check=True)
        if res is None: return None
        else:
            soup = BeautifulSoup(unquote(res['data']), 'html.parser')
            try:
                summary = soup.find_all("div", class_="prt-status-summary")[0].findChildren("div", class_="prt-status-value", recursive=True)
                data = {}
                data['count'] = int(summary[0].string)
                data['average'] = int(summary[1].string)
                data['online'] = int(summary[2].string)
                return data
            except:
                return None

    def getCrewData(self, target, mode=0): # retrieve a crew data (mode=0 - all, 1 - main page data only, 2 - main page and summary | add 10 to skip the cache check)
        if not self.bot.gbf.isAvailable(): # check for maintenance
            return {'error':'Game is in maintenance'}
        if isinstance(target, list) or isinstance(target, tuple): id = " ".join(target)
        elif isinstance(target, int): id = str(target)
        else: id = target
        crew_id_list = {**(self.bot.data.config['granblue']['gbfgcrew']), **(self.bot.data.config['granblue'].get('othercrew', {}))}
        id = crew_id_list.get(id.lower(), id) # check if the id is a gbfgcrew
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

        if mode >= 10:
            skipcache = True
            mode -= 10
        else: skipcache = False

        crew = {'scores':[], 'id':id}
        if not skipcache and id in self.crewcache: # public crews are stored until next reboot (to limit the request amount)
            crew = self.crewcache[id]
            if mode > 0: return crew
        else:
            for i in range(0, 4): # for each page (page 0 being the crew page, 1 to 3 being the crew page
                if i > 0 and mode > 0: break
                get = self.requestCrew(id, i)
                if get == "Maintenance":
                    return {'error':'Maintenance'}
                elif get == "Down":
                    return {'error':'Unavailable'}
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
                        crew['ship_element'] = {"10001":"wind", "20001":"fire", "30001":"water", "40001":"earth", "50001":"light", "60001":"dark"}.get(get['ship_img'].split('_')[0], 'gw')
                        crew['leader'] = su.unescape(get['leader_name'])
                        crew['leader_id'] = get['leader_user_id']
                        crew['donator'] = su.unescape(get['most_donated_name'])
                        crew['donator_id'] = get['most_donated_id']
                        crew['donator_amount'] = get['most_donated_lupi']
                        crew['message'] = su.unescape(get['introduction'])
                    else:
                        if 'player' not in crew: crew['player'] = []
                        for p in get['list']:
                            crew['player'].append({'id':p['id'], 'name':su.unescape(p['name']), 'level':p['level'], 'is_leader':p['is_leader'], 'member_position':p['member_position'], 'honor':None}) # honor is a placeholder
            
            if mode == 1: return crew
            data = self.getCrewSummary(id)
            if data is not None:
                crew = {**crew, **data}
            if mode > 0: return crew
            if not crew['private']: self.crewcache[id] = crew # only cache public crews


        # get the last gw score
        crew['scores'] = []
        data = self.searchGWDBCrew(id, 2)
        if data is not None:
            for n in range(0, 2):
                if data[n] is not None and 'result' in data[n] and len(data[n]['result']) == 1:
                    if data[n].get('ver', 0) == 2:
                        possible = {7:"Total Day 4", 6:"Total Day 3", 5:"Total Day 2", 4:"Total Day 1", 3:"Total Prelim."}
                        last_id = 7
                    else:
                        possible = {11:"Total Day 4", 9:"Total Day 3", 7:"Total Day 2", 5:"Total Day 1", 3:"Total Prelim."}
                        last_id = 11
                    for ps in possible:
                        if data[n]['result'][0][ps] is not None:
                            if ps == last_id and data[n]['result'][0][0] is not None:
                                crew['scores'].append("{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors ".format(self.bot.emote.get('gw'), data[n].get('gw', ''), data[n]['result'][0][0], data[n]['result'][0][ps]))
                                break
                            else:
                                crew['scores'].append("{} GW**{}** ▫️ {} ▫️ **{:,}** honors ".format(self.bot.emote.get('gw'), data[n].get('gw', ''), possible[ps], data[n]['result'][0][ps]))
                                break

        return crew

    def processCrewData(self, crew, mode=0):
        # embed initialization
        title = "\u202d{} **{}**".format(self.bot.emote.get(crew['ship_element']), crew['name'])
        if 'count' in crew: title += "▫️{}/30".format(crew['count'])
        if 'average' in crew: title += "▫️Rank {}".format(crew['average'])
        if 'online' in crew: title += "▫️{} online".format(crew['online'])
        description = "💬 `{}`".format(self.escape(crew['message'], True))
        footer = ""
        fields = []

        # append GW scores if any
        for s in crew['scores']:
            description += "\n{}".format(s)

        if crew['private']:
            description += '\n{} [{}](http://game.granbluefantasy.jp/#profile/{}) ▫️ *Crew is private*'.format(self.bot.emote.get('captain'), crew['leader'], crew['leader_id'])
        else:
            footer = "Public crews are updated once per day"
            # get GW data
            if mode == 2: gwstate = True
            elif mode == 1: gwstate = False
            else: gwstate = self.isGWRunning()
            players = crew['player'].copy()
            gwid = None
            if gwstate:
                total = 0
                unranked = 0
                for i in range(0, len(players)):
                    # retrieve player honors
                    honor = self.searchGWDBPlayer(players[i]['id'], 2)
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
                    description += "\n{} GW**{}** ▫️ Player Sum **{}** ▫️ Average **{}**".format(self.bot.emote.get('question'), gwid, self.honorFormat(total), self.honorFormat(total // (len(players) - unranked)))
                    if unranked > 0:
                        description += " ▫️ {} Unranked".format(unranked)
                        if unranked > 1: description += "s"
            # create the fields
            i = 0
            for p in players:
                if i % 10 == 0: fields.append({'name':'Page {}'.format(self.bot.emote.get('{}'.format(len(fields)+1))), 'value':''})
                i += 1
                if p['member_position'] == "1": r = "captain"
                elif p['member_position'] == "2": r = "foace"
                elif p['member_position'] == "3": r = "atkace"
                elif p['member_position'] == "4": r = "deface"
                else: r = "ensign"
                entry = '{} [{}](http://game.granbluefantasy.jp/#profile/{})'.format(self.bot.emote.get(r), self.escape(p['name']), p['id'])
                if gwstate:  entry += " \▫️ {}".format(self.honorFormat(p['honor']))
                else: entry += " \▫️ r**{}**".format(p['level'])
                entry += "\n"
                fields[-1]['value'] += entry
        return title, description, fields, footer

    async def postCrewData(self, ctx, id, mode = 0): # mode 0 = auto, 1 = gw mode disabled, 2 = gw mode enabled
        try:
            # retrieve formatted crew data
            await self.bot.util.react(ctx.message, 'time')
            crew = await self.bot.do(self.getCrewData, id, mode)

            if 'error' in crew: # print the error if any
                if len(crew['error']) > 0:
                    await ctx.reply(embed=self.bot.util.embed(title="Crew Error", description=crew['error'], color=self.color))
                await self.bot.util.unreact(ctx.message, 'time')
                return

            title, description, fields, footer = await self.bot.do(self.processCrewData, crew, mode)

            await self.bot.util.unreact(ctx.message, 'time')
            final_msg = await ctx.reply(embed=self.bot.util.embed(title=title, description=description, fields=fields, inline=True, url="http://game.granbluefantasy.jp/#guild/detail/{}".format(crew['id']), footer=footer, timestamp=crew['timestamp'], color=self.color))
            await self.bot.util.clean(ctx, final_msg, 60)

        except Exception as e:
            await self.bot.util.unreact(ctx.message, 'time')
            await self.bot.sendError("postCrewData", e)

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

    def _sortMembers(self, members):
        for i in range(0, len(members)-1):
            for j in range(i, len(members)):
                if int(members[i][2]) < int(members[j][2]):
                    tmp = members[i]
                    members[i] = members[j]
                    members[j] = tmp
        return members

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['supercrew', 'poaching'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gwranking(self, ctx):
        """Sort and post the top 30 server members per contribution"""
        members = []
        gwid = None
        await self.bot.util.react(ctx.message, 'time')
        for sid in self.bot.data.save['gbfids']:
            m = ctx.guild.get_member(int(sid))
            if m is not None:
                pdata = await self.bot.do(self.searchGWDBPlayer, self.bot.data.save['gbfids'][sid], 2)
                if pdata is not None and pdata[1] is not None and 'result' in pdata[1] and len(pdata[1]['result']) == 1:
                    if gwid is None: gwid = pdata[1].get('gw', None)
                    members.append([pdata[1]['result'][0][1], pdata[1]['result'][0][2], pdata[1]['result'][0][3]]) # id, name, honor
        await self.bot.util.unreact(ctx.message, 'time')
        if len(members) == 0:
            await ctx.send(embed=self.bot.util.embed(title="{} Top 30 of {}".format(self.bot.emote.get('gw'), ctx.guild.name), description="Unavailable", inline=True, thumbnail=ctx.guild.icon_url, color=self.color))
            return
        members = await self.bot.do(self._sortMembers, members)
        fields = []
        total = 0
        for i in range(0, min(30, len(members))):
            if i % 10 == 0:
                fields.append({'name':'{}'.format(self.bot.emote.get(str(len(fields)+1))), 'value':''})
            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{}) \▫️ **{}**\n".format(members[i][1], members[i][0], self.honorFormat(members[i][2]))
            total += members[i][2]
        if gwid is None: gwid = ""
        final_msg = await ctx.send(embed=self.bot.util.embed(author={'name':"Top 30 of {}".format(ctx.guild.name), 'icon_url':ctx.guild.icon_url}, description="{} GW**{}** ▫️ Player Total **{}** ▫️ Average **{}**".format(self.bot.emote.get('question'), gwid, self.honorFormat(total), self.honorFormat(total // min(30, len(members)))), fields=fields, inline=True, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    def getCrewLeaders(self, crews):
        if 'leadertime' not in self.bot.data.save['gbfdata'] or 'leader' not in self.bot.data.save['gbfdata'] or self.bot.util.JST() - self.bot.data.save['gbfdata']['leadertime'] > timedelta(days=6) or len(crews) != len(self.bot.data.save['gbfdata']['leader']):
            leaders = {}
            for c in crews:
                crew = self.getCrewData(c, 1)
                if 'error' in crew:
                    continue
                leaders[str(c)] = [crew['name'], crew['leader'], crew['leader_id']]
            with self.bot.data.lock:
                self.bot.data.save['gbfdata']['leader'] = leaders
                self.bot.data.save['gbfdata']['leadertime'] = self.bot.util.JST()
                self.bot.data.pending = True
        return self.bot.data.save['gbfdata']['leader']

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["resetdancho"])
    @isOwner()
    async def resetleader(self, ctx):
        """Reset the saved captain list (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['gbfdata'].pop('leader')
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["danchouranking", "danchous", "danchos", "captains", "captainranking", "capranking"])
    @commands.cooldown(1, 100, commands.BucketType.guild)
    async def danchoranking(self, ctx):
        """Sort and post all /gbfg/ captains per contribution"""
        crews = []
        await self.bot.util.react(ctx.message, 'time')
        for e in self.bot.data.config['granblue']['gbfgcrew']:
            if self.bot.data.config['granblue']['gbfgcrew'][e] in crews: continue
            crews.append(self.bot.data.config['granblue']['gbfgcrew'][e])
        ranking = []
        leaders = await self.bot.do(self.getCrewLeaders, crews)
        for cid in leaders:
            data = await self.bot.do(self.searchGWDBPlayer, leaders[cid][2], 2)
            if data is None or data[1] is None:
                continue
            gwid = data[1].get('gw', None)
            if len(data[1]['result']) == 0:
                ranking.append([leaders[cid][0], leaders[cid][1], None])
            else:
                ranking.append([leaders[cid][0], leaders[cid][1], data[1]['result'][0][3]])
        await self.bot.util.unreact(ctx.message, 'time')
        if len(ranking) == 0:
            final_msg = await ctx.send(embed=self.bot.util.embed(title="{} /gbfg/ Dancho Ranking".format(self.bot.emote.get('gw')), description="Unavailable", color=self.color))
        else:
            for i in range(len(ranking)): # sorting
                for j in range(i+1, len(ranking)):
                    if ranking[j][2] is not None and (ranking[i][2] is None or ranking[i][2] < ranking[j][2]):
                        tmp = ranking[i]
                        ranking[i] = ranking[j]
                        ranking[j] = tmp
            fields = []
            if gwid is None: gwid = ""
            for i in range(0, len(ranking)):
                if i % 15 == 0: fields.append({'name':'{}'.format(self.bot.emote.get(str(len(fields)+1))), 'value':''})
                if ranking[i][2] is None:
                    fields[-1]['value'] += "{} \▫️ {} \▫️ {} \▫️ **n/a**\n".format(i+1, ranking[i][1], ranking[i][0])
                else:
                    fields[-1]['value'] += "{} \▫️ {} \▫️ {} \▫️ **{}**\n".format(i+1, ranking[i][1], ranking[i][0], self.honorFormat(ranking[i][2]))
            final_msg = await ctx.send(embed=self.bot.util.embed(title="{} /gbfg/ GW{} Dancho Ranking".format(self.bot.emote.get('gw'), gwid), fields=fields, inline=True, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    def _gbfgranking(self):
        crews = []
        for e in self.bot.data.config['granblue']['gbfgcrew']:
            if self.bot.data.config['granblue']['gbfgcrew'][e] in crews: continue
            crews.append(self.bot.data.config['granblue']['gbfgcrew'][e])
        tosort = {}
        data = self.GWDBver()
        if data is None or data[1] is None:
            return None, None
        else:
            if data[1].get('ver', 0) != 2:
                possible = {11:"Total Day 4", 9:"Total Day 3", 7:"Total Day 2", 5:"Total Day 1", 3:"Total Prelim."}
                last_id = 11
                gwid = data[1].get('gw', None)
            else:
                possible = {7:"Total Day 4", 6:"Total Day 3", 5:"Total Day 2", 4:"Total Day 1", 3:"Total Prelim."}
                last_id = 7
                gwid = data[1].get('gw', None)
            for c in crews:
                data = self.searchGWDBCrew(int(c), 2)
                if data is None or data[1] is None or 'result' not in data[1] or len(data[1]['result']) == 0:
                    continue
                result = data[1]['result'][0]
                for ps in possible:
                    if result[ps] is not None:
                        if ps == last_id and result[0] is not None:
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
                if i % 15 == 0: fields.append({'name':'{}'.format(self.bot.emote.get(str(len(fields)+1))), 'value':''})
                if sorted[i][3].startswith('Total'):
                    fields[-1]['value'] += "{} \▫️ {} \▫️ **{}**\n".format(i+1, sorted[i][1], self.honorFormat(sorted[i][2]))
                else:
                    fields[-1]['value'] += "#**{}** \▫️ {} \▫️ **{}**\n".format(self.honorFormat(sorted[i][3]), sorted[i][1], self.honorFormat(sorted[i][2]))
            return fields, gwid

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gbfgranking(self, ctx):
        """Sort and post all /gbfg/ crew per contribution"""
        await self.bot.util.react(ctx.message, 'time')
        fields, gwid = await self.bot.do(self._gbfgranking)
        await self.bot.util.unreact(ctx.message, 'time')
        if fields is None:
            final_msg = await ctx.send(embed=self.bot.util.embed(title="{} /gbfg/ GW Ranking".format(self.bot.emote.get('gw')), description="Unavailable", color=self.color))
        else:
            final_msg = await ctx.send(embed=self.bot.util.embed(title="{} /gbfg/ GW{} Ranking".format(self.bot.emote.get('gw'), gwid), fields=fields, inline=True, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    def _recruit(self):
        crews = []
        for e in self.bot.data.config['granblue']['gbfgcrew']:
            if self.bot.data.config['granblue']['gbfgcrew'][e] in crews: continue
            crews.append(self.bot.data.config['granblue']['gbfgcrew'][e])

        sortedcrew = []
        for c in crews:
            data = self.getCrewData(int(c), 2)
            if 'error' not in data and data['count'] != 30:
                if len(sortedcrew) == 0: sortedcrew.append(data)
                else:
                    inserted = False
                    for i in range(len(sortedcrew)):
                        if data['average'] >= sortedcrew[i]['average']:
                            sortedcrew.insert(i, data)
                            inserted = True
                            break
                    if not inserted: sortedcrew.append(data)
        return sortedcrew

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['recruiting', 'opencrew', 'opencrews'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def recruit(self, ctx):
        """Post all recruiting /gbfg/ crews"""
        if not await self.bot.do(self.bot.gbf.isAvailable): # NOTE: slow?
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} /gbfg/ recruiting crews".format(self.bot.emote.get('crew')), description="Unavailable", color=self.color))
        else:
            await self.bot.util.react(ctx.message, 'time')
            sortedcrew = await self.bot.do(self._recruit)
            await self.bot.util.unreact(ctx.message, 'time')
            fields = []
            if len(sortedcrew) > 20: size = 15
            elif len(sortedcrew) > 10: size = 10
            else: size = 5
            for i in range(0, len(sortedcrew)):
                if i % size == 0: fields.append({'name':'{}'.format(self.bot.emote.get(str(len(fields)+1))), 'value':''})
                fields[-1]['value'] += "Rank **{}** \▫️  **{}** \▫️ **{}** slot\n".format(sortedcrew[i]['average'], sortedcrew[i]['name'], 30-sortedcrew[i]['count'])
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} /gbfg/ recruiting crews".format(self.bot.emote.get('crew')), fields=fields, inline=True, color=self.color, timestamp=self.bot.util.timestamp()))
        await self.bot.util.clean(ctx, final_msg, 90)

    def requestCrew(self, id : int, page : int): # get crew data
        if page == 0: return self.bot.gbf.request("http://game.granbluefantasy.jp/guild_other/guild_info/{}?PARAMS".format(id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check=True)
        else: return self.bot.gbf.request("http://game.granbluefantasy.jp/guild_other/member_list/{}/{}?PARAMS".format(page, id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check=True)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwlead', 'gwcompare', 'gwcmp'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def lead(self, ctx, IDcrewA : str, IDcrewB : str):
        """Search two crew current scores and compare them"""
        day = self.bot.ranking.getCurrentGWDayID()
        if day is None or (day % 10) <= 1:
            await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Unavailable", color=self.color))
            return
        if day >= 10: day = day % 10
        ver = None
        msg = ""
        lead = None
        crew_id_list = {**(self.bot.data.config['granblue']['gbfgcrew']), **(self.bot.data.config['granblue'].get('othercrew', {}))}
        for sid in [IDcrewA, IDcrewB]:
            if sid.lower() in crew_id_list:
                id = crew_id_list[sid.lower()]
            else:
                try: id = int(sid)
                except:
                    await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Invalid name `{}`".format(sid), color=self.color))
                    return

            data = await self.bot.do(self.searchGWDBCrew, str(id), 2)
            if data is None:
                await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Unavailable", color=self.color))
                return
            else:
                if data[1] is None or data[1].get('gw', '') != self.bot.data.save['gw']['id']:
                    await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="No data available for the current GW", color=self.color))
                    return
                result = data[1].get('result', [])
                ver = data[1].get('ver', 0)
                gwnum = data[1].get('gw', '')
                if len(result) == 0:
                    msg += "Crew [{}](http://game.granbluefantasy.jp/#guild/detail/{}) not found\n".format(sid, id)
                    lead = -1
                elif ver == 2:
                    d = [4, 5, 6, 7]
                    msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ {:,}\n".format(result[0][2], id, result[0][d[day-2]]-result[0][d[day-2]-1])
                    if lead is None: lead = result[0][d[day-2]]-result[0][d[day-2]-1]
                    elif lead >= 0: lead = abs(lead - (result[0][d[day-2]]-result[0][d[day-2]-1]))
                else:
                    d = [4, 6, 8, 10]
                    msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ {:,}\n".format(result[0][2], id, result[0][d[day-2]])
                    if lead is None: lead = result[0][d[day-2]]
                    elif lead >= 0: lead = abs(lead - result[0][d[day-2]])
        if lead is not None and lead >= 0:
            msg += "**Difference** ▫️ {:,}\n".format(lead)
        await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War {} ▫️ Day {}**".format(self.bot.emote.get('gw'), gwnum, day - 1), description=msg, timestamp=self.bot.util.timestamp(), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isYou()
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def youlead(self, ctx, opponent : str = ""):
        """Show the current match of (You)
        (You) Server Only"""
        if opponent != "":
            if not self.bot.isMod(ctx):
                await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Only moderators can set the opponent", color=self.color))
                return
            crew_id_list = {**(self.bot.data.config['granblue']['gbfgcrew']), **(self.bot.data.config['granblue'].get('othercrew', {}))}
            if opponent.lower() in crew_id_list:
                id = crew_id_list[opponent.lower()]
            else:
                try: id = int(opponent)
                except:
                    await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Invalid name `{}`".format(opponent), color=self.color))
                    return
            if self.bot.data.save['matchtracker'] is None or self.bot.data.save['matchtracker']['id'] != id:
                self.bot.data.save['matchtracker'] = {
                    'day':None,
                    'init':False,
                    'id':id,
                    'plot':[]
                }
            await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Opponent set to id `{}`, please wait the next ranking update".format(id), color=self.color))
        else:
            if self.bot.data.save['matchtracker'] is None or not self.bot.data.save['matchtracker']['init']:
                await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Unavailable, either wait the next ranking update or add the opponent id after the command to initialize it", color=self.color))
            else:
                you_id = self.bot.data.config['granblue']['gbfgcrew'].get('you', None)
                d = self.bot.util.JST() - self.bot.data.save['matchtracker']['last']
                msg = "Updated: **{}** ago".format(self.bot.util.delta2str(d, 0))
                if d.seconds >= 1200 and d.seconds <= 1800: msg += " ▫ *updating*"
                msg += "\n"
                end_time = self.bot.data.save['matchtracker']['last'].replace(day=self.bot.data.save['matchtracker']['last'].day+1, hour=0, minute=0, second=0, microsecond=0)
                remaining = end_time - self.bot.data.save['matchtracker']['last']
                msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ **{:,}**".format(self.bot.data.save['matchtracker']['names'][0], you_id, self.bot.data.save['matchtracker']['scores'][0])
                if self.bot.data.save['matchtracker']['speed'] is not None:
                    if self.bot.data.save['matchtracker']['speed'][0] == self.bot.data.save['matchtracker']['top_speed'][0]:
                        msg += "\n**Speed** ▫️ **Now {}/m** ▫️ **Top {}/m**".format(self.honorFormat(self.bot.data.save['matchtracker']['speed'][0]), self.honorFormat(self.bot.data.save['matchtracker']['top_speed'][0]))
                    else:
                        msg += "\n**Speed** ▫ Now {}/m ▫️ Top {}/m".format(self.honorFormat(self.bot.data.save['matchtracker']['speed'][0]), self.honorFormat(self.bot.data.save['matchtracker']['top_speed'][0]))
                    if end_time > self.bot.data.save['matchtracker']['last']:
                        msg += "\n**Estimation** ▫ Now {} ▫️ Top {}".format(self.honorFormat(self.bot.data.save['matchtracker']['scores'][0] + self.bot.data.save['matchtracker']['speed'][0] * remaining.seconds//60), self.honorFormat(self.bot.data.save['matchtracker']['scores'][0] + self.bot.data.save['matchtracker']['top_speed'][0] * remaining.seconds//60))
                msg += "\n\n"
                msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ **{:,}**".format(self.bot.data.save['matchtracker']['names'][1], self.bot.data.save['matchtracker']['id'], self.bot.data.save['matchtracker']['scores'][1])
                if self.bot.data.save['matchtracker']['speed'] is not None:
                    if self.bot.data.save['matchtracker']['speed'][1] == self.bot.data.save['matchtracker']['top_speed'][1]:
                        msg += "\n**Speed** ▫️ **Now {}/m** ▫️ **Top {}/m**".format(self.honorFormat(self.bot.data.save['matchtracker']['speed'][1]), self.honorFormat(self.bot.data.save['matchtracker']['top_speed'][1]))
                    else:
                        msg += "\n**Speed** ▫️ Now {}/m ▫️ Top {}/m".format(self.honorFormat(self.bot.data.save['matchtracker']['speed'][1]), self.honorFormat(self.bot.data.save['matchtracker']['top_speed'][1]))
                    if end_time > self.bot.data.save['matchtracker']['last']:
                        msg += "\n**Estimation** ▫ Now {} ▫️ Top {}".format(self.honorFormat(self.bot.data.save['matchtracker']['scores'][1] + self.bot.data.save['matchtracker']['speed'][1] * remaining.seconds//60), self.honorFormat(self.bot.data.save['matchtracker']['scores'][1] + self.bot.data.save['matchtracker']['top_speed'][1] * remaining.seconds//60))
                msg += "\n\n"
                lead = abs(self.bot.data.save['matchtracker']['scores'][0] - self.bot.data.save['matchtracker']['scores'][1])
                if lead >= 0:
                    msg += "**Difference** ▫️ {:,}\n".format(lead)

                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} **Guild War {} ▫️ Day {}**".format(self.bot.emote.get('gw'), self.bot.data.save['matchtracker']['gwid'], self.bot.data.save['matchtracker']['day']-1), description=msg, timestamp=self.bot.util.timestamp(), thumbnail=self.bot.data.save['matchtracker'].get('chart', None), color=self.color))
                await self.bot.util.clean(ctx, final_msg, 90)