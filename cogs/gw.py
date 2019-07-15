import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import json

class GW(commands.Cog):
    """GW related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xf4426e
        self.day_list = []

    def startTasks(self):
        self.bot.runTask('check_buff', self.checkGWBuff)

    async def checkGWBuff(self): # automatically calls the GW buff used by the (you) crew
        self.getGWState()
        if self.bot.gw['state'] == False: return
        await asyncio.sleep(3)
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="checkgwbuff() started", footer="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST())))
        try:
            guild = self.bot.get_guild(self.bot.ids['you_server'])
            channel = self.bot.get_channel(self.bot.ids['you_announcement'])
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
                                msg += self.bot.getEmoteStr(r[1]) + ' ' + r[0].mention + ' '
                        if self.bot.gw['buffs'][0][2]:
                            msg += self.bot.getEmoteStr('foace') + ' ' + fo_role.mention + ' '
                        if self.bot.gw['buffs'][0][4]:
                            if self.bot.gw['buffs'][0][3]:
                                msg += '**DOUBLE** buffs in 5 minutes'
                            else:
                                msg += '**DOUBLE** buffs now!'
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
                    if len(msg) > 0:
                        await channel.send(msg)
                        msg = ""
                    if len(self.bot.gw['buffs']) > 0:
                        d = self.bot.gw['buffs'][0][0] - current_time
                        if d.seconds > 1:
                            await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="checkgwbuff()", description="Checking buffs in **" + self.getTimedeltaStr(d) + "**\nNext buffs setting: [" + str(self.bot.gw['buffs'][0][1]) + ' ' + str(self.bot.gw['buffs'][0][2]) + ' ' + str(self.bot.gw['buffs'][0][3])+ ' ' + str(self.bot.gw['buffs'][0][4]) + "]\nBuffs in **" + self.getTimedeltaStr(d, True) + "**", footer="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST())))
                            await asyncio.sleep(d.seconds-1)
            if len(msg) > 0:
                await channel.send(msg)
        except asyncio.CancelledError:
            await self.bot.sendError('checkgwbuff', 'cancelled')
        except Exception as e:
            await self.bot.sendError('checkgwbuff', str(e))
        await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="checkgwbuff() ended", footer="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST())))

    def buildDayList(self): # used by the gw schedule command
        self.day_list = [
            [self.bot.getEmoteStr('kmr') + " Ban Wave", "BW", ""],
            [self.bot.getEmoteStr('gold') + " Preliminaries", "Preliminaries", "Interlude"],
            [self.bot.getEmoteStr('wood') + " Interlude", "Interlude", "Day 1"],
            [self.bot.getEmoteStr('1') + " Day 1", "Day 1", "Day 2"],
            [self.bot.getEmoteStr('2') + " Day 2", "Day 2", "Day 3"],
            [self.bot.getEmoteStr('3') + " Day 3", "Day 3", "Day 4"],
            [self.bot.getEmoteStr('4') + " Day 4", "Day 4", "Day 5"],
            [self.bot.getEmoteStr('red') + " Final Rally", "Day 5", "End"]
        ]

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    def isYouServer(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isYouServer(ctx)
        return commands.check(predicate)

    def isAuthorizedSpecial(): # for decorators
        async def predicate(ctx):
            return (ctx.bot.isYouServer(ctx) or ctx.bot.isAuthorized(ctx))
        return commands.check(predicate)

    def getTimedeltaStr(self, delta, day=False):
        if day: return str(delta.days) + "d" + str(delta.seconds // 3600) + "h" + str((delta.seconds // 60) % 60) + "m"
        else: return str(delta.seconds // 3600) + "h" + str((delta.seconds // 60) % 60) + "m"

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
                return self.bot.getEmoteStr('time') + " Guild War starts in **" + self.getTimedeltaStr(d, True) + "**"
            elif current_time >= self.bot.gw['dates']["End"]:
                self.bot.gw['state'] = False
                self.bot.gw['dates'] = {}
                self.bot.cancelTask('gwtask')
                self.bot.savePending = True
                return ""
            elif current_time > self.bot.gw['dates']["Day 5"]:
                d = self.bot.gw['dates']["End"] - current_time
                return self.bot.getEmoteStr('mark_a') + " Final Rally is on going\n" + self.bot.getEmoteStr('time') + " Guild War ends in **" + self.getTimedeltaStr(d) + "**"
            elif current_time > self.bot.gw['dates']["Day 1"]:
                it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
                for i in range(1, len(it)): # loop to not copy paste this 5 more times
                    if current_time > self.bot.gw['dates'][it[i]]:
                        d = self.bot.gw['dates'][it[i-1]] - current_time
                        if d < timedelta(seconds=25200): msg = self.bot.getEmoteStr('mark_a') + " " + it[i] + " ended"
                        else: msg = self.bot.getEmoteStr('mark_a') + " " + it[i] + " is on going (Time left: **" + self.getTimedeltaStr(self.bot.gw['dates'][it[i]] + timedelta(seconds=61200) - current_time) + "**)"
                        if i == 1: return msg + "\n" + self.bot.getEmoteStr('time') + " " + it[i-1].replace('Day 5', 'Final Rally') + " starts in **" + self.getTimedeltaStr(d) + "**"
                        else: return msg + "\n" + self.bot.getEmoteStr('time') + " " + it[i-1] + " starts in **" + self.getTimedeltaStr(d) + "**"
            elif current_time > self.bot.gw['dates']["Interlude"]:
                d = self.bot.gw['dates']["Day 1"] - current_time
                return self.bot.getEmoteStr('mark_a') + " Interlude is on going\n" + self.bot.getEmoteStr('time') + " Day 1 starts in **" + self.getTimedeltaStr(d) + "**"
            elif current_time > self.bot.gw['dates']["Preliminaries"]:
                d = self.bot.gw['dates']['Interlude'] - current_time
                if d < timedelta(seconds=104400): msg = self.bot.getEmoteStr('mark_a') + " Preliminaries ended"
                else: msg = self.bot.getEmoteStr('mark_a') + " Preliminaries is on going (Time left: **" + self.getTimedeltaStr(self.bot.gw['dates']["Preliminaries"] + timedelta(seconds=104400) - current_time, True) + "**)"
                return msg + "\n" + self.bot.getEmoteStr('time') + " Interlude starts in **" + self.getTimedeltaStr(d, True) + "**"
            else:
                return ""
        else:
            return ""

    def getNextBuff(self, ctx): # for the (you) crew, get the next set of buffs to be called
        if self.bot.gw['state'] == True:
            current_time = self.bot.getJST()
            if current_time < self.bot.gw['dates']["Preliminaries"]:
                return ""
            for b in self.bot.gw['buffs']:
                if not b[3] and current_time < b[0]:
                    msg = self.bot.getEmoteStr('question') + " Next buffs in **" + self.getTimedeltaStr(b[0] - current_time, True) + "** ("
                    if b[1]:
                        msg += "Attack " + self.bot.getEmoteStr('atkace') + ", Defense " + self.bot.getEmoteStr('deface')
                        if b[2]:
                            msg += ", FO " + self.bot.getEmoteStr('foace')
                    elif b[2]:
                        msg += "FO " + self.bot.getEmoteStr('foace')
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
                title = self.bot.getEmoteStr('gw') + " **Guild War** :black_small_square: Time: **{0:%m/%d %H:%M}**\n".format(current_time)
                description = ""
                if len(self.day_list) == 0:
                    self.buildDayList()
                if current_time < self.bot.gw['dates']["End"]:
                    for it in self.day_list:
                        if it[1] == "BW":
                            d = self.bot.gw['dates']["Preliminaries"] - timedelta(days=random.randint(1, 4))
                            if current_time < d and random.randint(1, 8) == 1:
                                description += it[0] + " **{0:%m/%d %H:%M}**\n".format(d)
                        else:
                            if self.dayCheck(current_time, self.bot.gw['dates'][it[2]], it[1]=="Day 5"):
                                description += it[0] + ": **{0:%m/%d %H:%M}**\n".format(self.bot.gw['dates'][it[1]])
                else:
                    await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " **Guild War**", description="Not available", color=self.color))
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
                    description += self.getNextBuff(ctx)
                except Exception as e:
                    await self.bot.sendError("getnextbuff", str(e))

                await ctx.send(embed=self.bot.buildEmbed(title=title, description=description, color=self.color))
            except Exception as e:
                await self.bot.sendError("gw", str(e))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " **Guild War**", description="Not available", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwtime'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def fugdidgwstart(self, ctx):
        """Check if GW started"""
        try:
            d = self.getGWState()
            if d != "":
                await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " Guild War status", description=d, color=self.color))
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
                await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " Guild War (You) Buff status", description=d, color=self.color))
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
            embed = discord.Embed(title=self.bot.getEmoteStr('gw') + " Guild Searcher", url="http://gbf.gw.lt/gw-guild-searcher/search", color=self.color) # random color
            embed.set_footer(text="crew history: searchid <crew id>")
            i = 0
            for c in data['result']:
                msg = "GW**" + str(c['data'][0]['gw_num']) + "** score: **" + "{:,}".format(c['data'][0]['points'])
                if c['data'][0]['is_seed']: msg += " (seeded)"
                msg += "**"
                embed.add_field(name=c["data"][0]["name"] + " ▪ " + msg, value="http://game.granbluefantasy.jp/#guild/detail/" + str(c['id']), inline=False)
                i += 1
                if i >= 5: break
            if len(data["result"]) > 5: 
                embed.add_field(name="5 / " + str(len(data["result"])) + " results shown", value="please go here for more: http://gbf.gw.lt/gw-guild-searcher/", inline=False)
            if i > 0: await ctx.send(embed=embed)
            else: await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " Guild Searcher", description="No Crews found", color=self.color))
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
                async with session.get("http://gbf.gw.lt/gw-guild-searcher/info/" + str(id)) as resp:
                    if resp.status != 200: raise Exception("HTTP Error " + str(resp.status))
                    data = json.loads(await resp.read())
            if len(data["data"]) == 0:
                await ctx.send(embed=self.bot.buildEmbed(title=self.bot.getEmoteStr('gw') + " Guild Searcher", description="Crew not found", color=self.color))
                return
            embed = discord.Embed(title=self.bot.getEmoteStr('gw') + " Guild Searcher", url="http://gbf.gw.lt/gw-guild-searcher/search", description=data["data"][0]["name"] + " ▪ http://game.granbluefantasy.jp/#guild/detail/" + str(data["id"]), color=random.randint(0, 16777216)) # random color
            i = 0
            for c in data["data"]:
                msg = "score: **" + "{:,}".format(c["points"])
                if c["is_seed"]: msg += " (seeded)**"
                else: msg += "**"
                embed.add_field(name="GW" + str(c["gw_num"]), value=msg, inline=True)
                i += 1
                if i >= 6: break
            if len(data["data"]) > 6: 
                embed.add_field(name="6 / " + str(len(data["data"])) + " past GWs shown", value="please go here for more: http://gbf.gw.lt/gw-guild-searcher/", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="The seach couldn't be completed", footer=str(e), color=self.color))
            await self.bot.sendError("searchid", str(e))