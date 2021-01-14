import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import json
import sqlite3
from xml.sax import saxutils as su

class GuildWar(commands.Cog):
    """GW related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xf4426e

    def startTasks(self):
        self.bot.runTask('check_buff', self.checkGWBuff)

    async def checkGWBuff(self): # automatically calls the GW buff used by the (you) crew
        self.getGWState()
        if self.bot.gw['state'] == False or len(self.bot.gw['buffs']) == 0: return
        await asyncio.sleep(3)
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
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="User task ended", description="check_buff", timestamp=datetime.utcnow()))

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

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def isYouServer(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isServer(ctx, 'you_server')
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
        if self.bot.gw['state'] == True:
            current_time = self.bot.getJST()
            if current_time < self.bot.gw['dates']["Preliminaries"]:
                d = self.bot.gw['dates']["Preliminaries"] - current_time
                return "{} Guild War starts in **{}**".format(self.bot.getEmote('gw'), self.bot.getTimedeltaStr(d, 2))
            elif current_time >= self.bot.gw['dates']["End"]:
                self.bot.gw['state'] = False
                self.bot.gw['dates'] = {}
                self.bot.cancelTask('gwtask')
                self.bot.matchtracker = None
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
                        else: msg = "{} GW {} is on going (Time left: **{}**)".format(self.bot.getEmote('mark_a'), it[i], self.bot.getTimedeltaStr(self.bot.gw['dates'][it[i]] + timedelta(seconds=61200) - current_time))
                        if i == 1: return "{}\n{} {} starts in **{}**".format(msg, self.bot.getEmote('time'), it[i-1].replace('Day 5', 'Final Rally'), self.bot.getTimedeltaStr(d))
                        else: return "{}\n{} {} starts in **{}**".format(msg, self.bot.getEmote('time'), it[i-1], self.bot.getTimedeltaStr(d))
            elif current_time > self.bot.gw['dates']["Interlude"]:
                d = self.bot.gw['dates']["Day 1"] - current_time
                return "{} Interlude is on going\n{} Day 1 starts in **{}**".format(self.bot.getEmote('mark_a'), self.bot.getEmote('time'), self.bot.getTimedeltaStr(d))
            elif current_time > self.bot.gw['dates']["Preliminaries"]:
                d = self.bot.gw['dates']['Interlude'] - current_time
                if d < timedelta(seconds=25200): msg = "{} Preliminaries ended".format(self.bot.getEmote('mark_a'))
                else: msg = "{} Preliminaries are on going (Time left: **{}**)".format(self.bot.getEmote('mark_a'), self.bot.getTimedeltaStr(self.bot.gw['dates']["Preliminaries"] + timedelta(seconds=104400) - current_time, 2))
                return "{}\n{} Interlude starts in **{}**".format(msg, self.bot.getEmote('time'), self.bot.getTimedeltaStr(d, 2))
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
                    if self.bot.gw['dates'][it[i-1]] - current_time < timedelta(seconds=25200): return None
                    return self.bot.gw['dates'][it[i]] + timedelta(seconds=61200) - current_time
            return None
        elif current_time > self.bot.gw['dates']["Interlude"]:
            return self.bot.gw['dates']["Day 1"] - current_time
        elif current_time > self.bot.gw['dates']["Preliminaries"]:
            if self.bot.gw['dates']["Interlude"] - current_time < timedelta(seconds=25200): return None
            return self.bot.gw['dates']["Preliminaries"] + timedelta(seconds=104400) - current_time
        return None

    def getNextBuff(self, ctx): # for the (you) crew, get the next set of buffs to be called
        if self.bot.gw['state'] == True and ctx.guild.id == self.bot.ids.get('you_server', 0):
            current_time = self.bot.getJST()
            if current_time < self.bot.gw['dates']["Preliminaries"]:
                return ""
            for b in self.bot.gw['buffs']:
                if not b[3] and current_time < b[0]:
                    msg = "{} Next buffs in **{}** (".format(self.bot.getEmote('question'), self.bot.getTimedeltaStr(b[0] - current_time, 2))
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
    async def GW(self, ctx, gmt :int = 9):
        """Post the GW schedule"""
        if self.bot.gw['state'] == True:
            try:
                if gmt < -12 or gmt > 14: gmt = 9
                current_time = self.bot.getJST()
                em = self.bot.getEmote(self.bot.gw.get('element', ''))
                if em == "": em = ":white_small_square:"
                title = "{} **Guild War {}** {} **{:%a. %m/%d %H:%M} TZ**\n".format(self.bot.getEmote('gw'), self.bot.gw['id'], em, current_time + timedelta(seconds=3600*(gmt-9)))
                if gmt == 9: title = title.replace('TZ', 'JST')
                elif gmt == 0: title = title.replace('TZ', 'GMT')
                else: title = title.replace('TZ', 'GMT{0:+}'.format(gmt))
                description = ""
                day_list = self.buildDayList()
                if current_time < self.bot.gw['dates']["End"]:
                    for it in day_list:
                        if it[1] == "BW":
                            d = self.bot.gw['dates']["Preliminaries"] - timedelta(days=random.randint(1, 4)) + timedelta(seconds=3600*(gmt-9))
                            if current_time < d and random.randint(1, 8) == 1:
                                description += it[0] + " **{:%a. %m/%d %H:%M}**\n".format(d)
                        else:
                            if self.dayCheck(current_time, self.bot.gw['dates'][it[2]], it[1]=="Day 5") or (it[1] == "Interlude" and self.dayCheck(current_time, self.bot.gw['dates'][it[2]] + timedelta(seconds=25200), False)):
                                description += it[0] + ": **{:%a. %m/%d %H:%M}**\n".format(self.bot.gw['dates'][it[1]] + timedelta(seconds=3600*(gmt-9)))
                else:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Not available", color=self.color))
                    self.bot.gw['state'] = False
                    self.bot.gw['dates'] = {}
                    self.bot.cancelTask('gwtask')
                    self.bot.matchtracker = None
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
                if em == "": em = ":white_small_square:"
                await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War {}** {} status".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description=d, color=self.color))
        except Exception as e:
            await ctx.reply(embed=self.bot.buildEmbed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("fugdidgwstart", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['buff'])
    @isYouServer()
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def GWbuff(self, ctx):
        """Check when is the next GW buff, (You) Only"""
        try:
            d = self.getNextBuff(ctx)
            if d != "":
                await ctx.reply(embed=self.bot.buildEmbed(title="{} Guild War (You) Buff status".format(self.bot.getEmote('gw')), description=d, color=self.color))
            else:
                await ctx.reply(embed=self.bot.buildEmbed(title="{} Guild War (You) Buff status".format(self.bot.getEmote('gw')), description="Only available when Guild War is on going", color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("gwbuff", str(e))

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
                if em == "": em = ""
                d = self.bot.getJST() - self.bot.gw['ranking'][4]
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {}".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description="Updated: **{}** ago".format(self.bot.getTimedeltaStr(d, 0)), fields=fields, footer="Update on minute 5, 25 and 45", inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("ranking", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['estimate', 'estim', 'predict', 'prediction'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def estimation(self, ctx):
        """Estimate the GW ranking at the end of current day"""
        try:
            if self.bot.gw['state'] == False or self.bot.getJST() < self.bot.gw['dates']["Preliminaries"] or self.bot.gw['ranking'] is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Estimation unavailable", color=self.color))
            else:
                em = self.bot.getEmote(self.bot.gw.get('element', ''))
                if em == "": em = ""
                current_time_left = self.getGWTimeLeft()
                if current_time_left is None:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {}".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description="Estimations are currently unavailable", inline=True, color=self.color))
                    return
                elif current_time_left.days > 0 or current_time_left.seconds > 21300:
                    current_time_left -= timedelta(seconds=21300)
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {}".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description="Estimations available in **{}**".format(self.bot.getTimedeltaStr(current_time_left)), inline=True, color=self.color))
                    return
                time_left = self.getGWTimeLeft(self.bot.gw['ranking'][4])
                time_modifier = (1.1 + 1.2 * (time_left.seconds // 3600) / 10)
                fields = [{'name':'**Crew Ranking**', 'value':''}, {'name':'**Player Ranking**', 'value':''}]
                for x in [0, 1]:
                    for c in self.bot.gw['ranking'][x]:
                        if c in self.bot.gw['ranking'][2+x] and self.bot.gw['ranking'][2+x][c] > 0:
                            predi = [0, 0]
                            for y in [0, 1]:
                                if y == 0: predi[y] = self.bot.gw['ranking'][x][c] + (1 + 1.5 * (time_left.seconds // 7200) / 10) + self.bot.gw['ranking'][2+x][c] * time_left.seconds / 60 # minimum
                                elif y == 1:  predi[y] = self.bot.gw['ranking'][x][c] + (1.1 + 1.3 * (time_left.seconds // 3600) / 10) * self.bot.gw['ranking'][2+x][c] * time_left.seconds / 60 # maximum
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
                d = self.bot.getJST() - self.bot.gw['ranking'][4]
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {}".format(self.bot.getEmote('gw'), self.bot.gw['id'], em), description="Time left: **{}** \▫️ Updated: **{}** ago\nThis is a simple estimation, take it with a grain of salt.".format(self.bot.getTimedeltaStr(current_time_left), self.bot.getTimedeltaStr(d, 0)), fields=fields, footer="Update on minute 5, 25 and 45", timestamp=datetime.utcnow(), inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("estimation", str(e))