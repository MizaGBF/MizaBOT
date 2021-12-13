from disnake.ext import commands
import asyncio
from datetime import datetime, timedelta
import random
import math
from bs4 import BeautifulSoup
import html
from urllib.parse import unquote
import statistics

# ----------------------------------------------------------------------------------------------------------------
# Guild War Cog
# ----------------------------------------------------------------------------------------------------------------
# Commands related to Unite and Fight and Granblue Fantasy Crews
# ----------------------------------------------------------------------------------------------------------------

class GuildWar(commands.Cog):
    """Unite & Fight and Crew commands."""
    guild_ids = []
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xff0000
        try: self.guild_ids.append(self.bot.data.config['ids']['you_server'])
        except: pass
        self.crewcache = {}

    def startTasks(self):
        self.bot.runTask('check_buff', self.checkGWBuff)
        self.bot.runTask('check_ranking', self.bot.ranking.checkGWRanking)

    """checkGWBuff()
    Bot Task managing the buff alert of the (You) server
    """
    async def checkGWBuff(self):
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
                                    msg += '*Buffs in* **5 minutes (Use twice this time! They are reset later.)**'
                                else:
                                    msg += 'Buffs now! **(Use twice this time! They are reset later.)**'
                            else:
                                if self.bot.data.save['gw']['buffs'][0][3]:
                                    msg += '*Buffs in* **5 minutes**'
                                else:
                                    msg += 'Buffs now!'
                            msg += "\nhttp://game.granbluefantasy.jp/#event/teamraid{}/guild_ability".format(str(self.bot.data.save['gw']['id']).zfill(3))
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

    """buildDayList()
    Generate the day list used by the gw command
    
    Returns
    --------
    list: List of lists containing: The day string, the day key and the next day key
    """
    def buildDayList(self): # used by the gw schedule command
        return [
            ["{} Automatic BAN Execution".format(self.bot.emote.get('kmr')), "BW", ""], # for memes
            ["{} Preliminaries".format(self.bot.emote.get('gold')), "Preliminaries", "Interlude"],
            ["{} Interlude".format(self.bot.emote.get('wood')), "Interlude", "Day 1"],
            ["{} Day 1".format(self.bot.emote.get('1')), "Day 1", "Day 2"],
            ["{} Day 2".format(self.bot.emote.get('2')), "Day 2", "Day 3"],
            ["{} Day 3".format(self.bot.emote.get('3')), "Day 3", "Day 4"],
            ["{} Day 4".format(self.bot.emote.get('4')), "Day 4", "Day 5"],
            ["{} Final Rally".format(self.bot.emote.get('red')), "Day 5", "End"]
        ]

    """isGWRunning()
    Check the GW state and returns if the GW is on going.
    Clear the data if it ended.
    
    Returns
    --------
    bool: True if it's running, False if it's not
    """
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

    """escape()
    Proper markdown escape player names
    
    Parameters
    ----------
    s: String to escape
    lite: If True, less escapes are applied
    
    Returns
    --------
    str: Escaped string
    """
    def escape(self, s, lite=False):
        # add the RLO character before
        x = html.unescape(s)
        if lite: return '\u202d' + x.replace('\\', '\\\\').replace('`', '\\`')
        else: return '\u202d' + x.replace('\\', '\\\\').replace('`', '\'').replace('*', '\\*').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('[', '').replace(']', '').replace('(', '\\(').replace(')', '\\)').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('|', '\\|')

    """htmlescape()
    Escape special characters into html notation (used for crew and player names)
    
    Parameters
    ----------
    s: String to escape
    
    Returns
    --------
    str: Escaped string
    """
    def htmlescape(self, s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace('\'', "&#039;")

    """dayCheck()
    Check if the we are in the specified GW day
    
    Parameters
    ----------
    current: Current time, JST
    day: Day to compare to
    final_day: If True, check for the final GW day (it's shorter)
    
    Returns
    --------
    bool: True if successful, False if not
    """
    def dayCheck(self, current, day, final_day=False):
        d = day - current
        if current < day and (final_day or d >= timedelta(seconds=25200)):
            return True
        return False

    """getGWState()
    Return the state of the Unite & Fight event
    
    Returns
    --------
    str: Unite & Fight state
    """
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

    """getGWTimeLeft()
    Return the time left until the next unite & fight day
    
    Returns
    --------
    timedelta: Time left or None if error
    """
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

    """getNextBuff()
    Return the time left until the next buffs for the (You) server
    
    Parameters
    ----------
    inter: Command interaction (to check the server)
    
    Returns
    --------
    str: Time left, empty if error
    """
    def getNextBuff(self, inter): # for the (you) crew, get the next set of buffs to be called
        if self.bot.data.save['gw']['state'] == True and inter.guild.id == self.bot.data.config['ids'].get('you_server', 0):
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

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 40, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def gw(self, inter, gmt : int = commands.Param(description='Your timezone from GMT', ge=-12, le=14, default=9, autocomplete=[-12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])):
        """Post the GW schedule"""
        if self.bot.data.save['gw']['state'] == True:
            try:
                current_time = self.bot.util.JST()
                em = self.bot.util.formatElement(self.bot.data.save['gw']['element'])
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
                    await inter.response.send_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Not available", color=self.color))
                    with self.bot.data.lock:
                        self.bot.data.save['gw']['state'] = False
                        self.bot.data.save['gw']['dates'] = {}
                        self.bot.cancelTask('check_buff')
                        self.bot.data.save['youtracker'] = None
                        self.bot.data.pending = True
                    await self.bot.util.clean(inter, 40)
                    return

                try:
                    description += self.getGWState()
                except Exception as e:
                    await self.bot.sendError("getgwstate", e)

                try:
                    description += '\n' + self.getNextBuff(inter)
                except Exception as e:
                    await self.bot.sendError("getnextbuff", e)

                await inter.response.send_message(embed=self.bot.util.embed(title=title, description=description, color=self.color))
            except Exception as e:
                await self.bot.sendError("gw", e)
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Not available", color=self.color))
            await self.bot.util.clean(inter, 40)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def gwbuff(self, inter):
        """Check when is the next GW buff ((You) Server Only)"""
        try:
            d = self.getNextBuff(inter)
            if d != "":
                await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War (You) Buff status".format(self.bot.emote.get('gw')), description=d, color=self.color))
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War (You) Buff status".format(self.bot.emote.get('gw')), description="Only available when Guild War is on going", color=self.color))
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color), ephemeral=True)
            await self.bot.sendError("gwbuff", e)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def ranking(self, inter):
        """Retrieve the current GW ranking"""
        try:
            if self.bot.data.save['gw']['state'] == False or self.bot.util.JST() < self.bot.data.save['gw']['dates']["Preliminaries"] or self.bot.data.save['gw']['ranking'] is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Ranking unavailable", color=self.color))
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
                        if c in self.bot.data.save['gw']['ranking'][2+x] and self.bot.data.save['gw']['ranking'][2+x][c] != 0:
                            fields[x]['value'] += " \▫️ {}/min".format(self.bot.util.valToStr(self.bot.data.save['gw']['ranking'][2+x][c]))
                        fields[x]['value'] += "\n"
                    if fields[x]['value'] == '': fields[0]['value'] = 'Unavailable'

                em = self.bot.util.formatElement(self.bot.data.save['gw']['element'])
                d = self.bot.util.JST() - self.bot.data.save['gw']['ranking'][4]
                await inter.response.send_message(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Updated: **{}** ago".format(self.bot.util.delta2str(d, 0)), fields=fields, footer="Update on minute 5, 25 and 45", timestamp=self.bot.util.timestamp(), inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("ranking", e)
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def estimation(self, inter):
        """Estimate the GW ranking at the end of current day"""
        try:
            if self.bot.data.save['gw']['state'] == False or self.bot.util.JST() < self.bot.data.save['gw']['dates']["Preliminaries"] or self.bot.data.save['gw']['ranking'] is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Estimation unavailable", color=self.color))
            else:
                em = self.bot.util.formatElement(self.bot.data.save['gw']['element'])
                current_time_left = self.getGWTimeLeft()
                if current_time_left is None:
                    await inter.response.send_message(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Estimations are currently unavailable", inline=True, color=self.color))
                    return
                elif current_time_left.days > 0 or current_time_left.seconds > 21300:
                    current_time_left -= timedelta(seconds=21300)
                    await inter.response.send_message(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Estimations available in **{}**".format(self.bot.util.delta2str(current_time_left)), inline=True, color=self.color))
                    return
                seconds_left = self.getGWTimeLeft(self.bot.data.save['gw']['ranking'][4]).seconds
                fields = [{'name':'**Crew Ranking**', 'value':''}, {'name':'**Player Ranking**', 'value':''}]
                modifiers = [
                    (1.00 + (0.7 * (seconds_left // 3600) + 0.5 * (seconds_left // 7200) + 0.4 * (seconds_left // 10800)) / 10), # minimum
                    (1.08 + (1.4 * (seconds_left // 3600) + 1.0 * (seconds_left // 7200) + 0.5 * (seconds_left // 10800)) / 10)  # maximum
                ]
                for x in [0, 1]:
                    for c in self.bot.data.save['gw']['ranking'][x]:
                        if c in self.bot.data.save['gw']['ranking'][2+x] and self.bot.data.save['gw']['ranking'][2+x][c] > 0:
                            predi = [0, 0]
                            for y in [0, 1]:
                                predi[y] = self.bot.data.save['gw']['ranking'][x][c] + modifiers[y] * self.bot.data.save['gw']['ranking'][2+x][c] * seconds_left / 60
                                if predi[y] >= 1000:
                                    predi[y] = self.bot.util.valToStrBig(predi[y])

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
                await inter.response.send_message(embed=self.bot.util.embed(title="{} **Guild War {}** {}".format(self.bot.emote.get('gw'), self.bot.data.save['gw']['id'], em), description="Time left: **{}** \▫️ Updated: **{}** ago\nThis is a simple estimation, take it with a grain of salt.".format(self.bot.util.delta2str(current_time_left), self.bot.util.delta2str(d, 0)), fields=fields, footer="Update on minute 5, 25 and 45", timestamp=self.bot.util.timestamp(), inline=True, color=self.color))
        except Exception as e:
            await self.bot.sendError("estimation", e)
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color), ephemeral=True)

    """findranking()
    Extract parameters from terms and call searchGWDB() with the proper settings.
    inter is used to output the result.
    Used by findgw()
    
    Parameters
    ----------
    inter: Command interaction
    type: Boolean, True for crews, False for players
    terms: Search string
    """
    async def findranking(self, inter, type, terms):
        # set the search strings based on the search type
        if type: txt = "crew"
        else: txt = "player"
        await inter.response.defer()
        
        if terms == "": # no search terms so we print how to use it
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="**Usage**\n`/findgw [{}name]` to search a {} by name\n`/findgw %eq [{}name]` or `/findgw %== [{}name]` for an exact match\n`/findgw %id [{}id]` for an id search\n`/findgw %rank [ranking]` for a ranking search\n`/findgw %all ...` to receive all the results by direct message".replace('{}', txt), color=self.color))
        else:
            try:
                # check if the %all option is included and extract it
                index = terms.find("%all ")
                if index != -1 and index + 5 < len(terms):
                    terms = terms.replace("%all ", "")
                    all = True
                else:
                    all = False

                # check if the %past option is included and extract it
                index = terms.find("%past ")
                if index != -1 and index + 6 < len(terms):
                    terms = terms.replace("%past ", "")
                    past = True
                else:
                    past = False

                # check if the %== or %eq options are included and extract it
                if terms.startswith("%== ") or terms.startswith("%eq "):
                    terms = self.htmlescape(terms[4:])
                    mode = 1
                elif terms.startswith("%id "):
                    try:
                        terms = int(terms[4:])
                        mode = 2
                    except:
                        await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                elif terms.startswith("%rank "):
                    try:
                        terms = int(terms[6:])
                        mode = 3
                    except:
                        await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                else:
                    mode = 0
                    terms = self.htmlescape(terms)

                # do our search
                data = await self.bot.do(self.bot.ranking.searchGWDB, terms, (mode+10 if type else mode))

                # select the right database (oldest one if %past is set or newest is unavailable, if not the newest)
                if data[1] is None or past: result = data[0]
                else: result = data[1]
                
                # check validity
                if result is None:
                    await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Database unavailable", color=self.color))
                    raise Exception("Returning")

                if len(result) == 0: # check number of matches
                    await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="`{}` not found".format(html.unescape(str(terms))), color=self.color))
                    raise Exception("Returning")
                elif all: # set number of results to send if %all if set
                    if type: xl = 36
                    else: xl = 80
                    x = len(result)
                    if x > xl: x = xl
                    await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Sending your {}/{} result(s)".format(x, len(result)), color=self.color))
                elif type and len(result) > 6: x = 6 # set number of crew results to send if greater than 6
                elif not type and len(result) > 15: x = 15 # set number of player results to send if greater than 15
                else: x = len(result) # else set the number of results to send equal to the available amount
                
                # embed fields for the message
                fields = []
                for i in range(0, x):
                    if type: # crew -----------------------------------------------------------------
                        fields.append({'name':"{}".format(html.unescape(result[i].name)), 'value':''})
                        if result[i].ranking is not None: fields[-1]['value'] += "▫️**#{}**\n".format(result[i].ranking)
                        else: fields[-1]['value'] += "\n"
                        if result[i].preliminaries is not None: fields[-1]['value'] += "**P.** ▫️{:,}\n".format(result[i].preliminaries)
                        if result[i].day1 is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('1'), result[i].day1)
                        if result[i].day2 is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('2'), result[i].day2)
                        if result[i].day3 is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('3'), result[i].day3)
                        if result[i].day4 is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.emote.get('4'), result[i].day4)
                        if fields[-1]['value'] == "": fields[-1]['value'] = "No data"
                        fields[-1]['value'] = "[{}](http://game.granbluefantasy.jp/#guild/detail/{}){}".format(result[i].id, result[i].id, fields[-1]['value'])
                        gwnum = result[i].gw
                        # sending via dm if %all is set
                        if all and ((i % 6) == 5 or i == x - 1):
                            try:
                                await inter.author.send(embed=self.bot.util.embed(title="{} **Guild War {}**".format(self.bot.emote.get('gw'), gwnum), fields=fields, inline=True, color=self.color))
                            except:
                                await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="I can't send you the full list by private messages", color=self.color))
                                raise Exception("Returning")
                            fields = []
                    else: # player -----------------------------------------------------------------
                        if i % 5 == 0:
                            fields.append({'name':'Page {}'.format(self.bot.emote.get(str(((i // 5) % 3) + 1))), 'value':''})
                        if result[i].ranking is None:
                            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{})\n".format(self.escape(result[i].name), result[i].id)
                        else:
                            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{}) ▫️ **#{}**\n".format(self.escape(result[i].name), result[i].id, result[i].ranking)
                        if result[i].current is not None: fields[-1]['value'] += "{:,}\n".format(result[i].current)
                        else: fields[-1]['value'] += "n/a\n"
                        gwnum = result[i].gw
                        # sending via dm if %all is set
                        if all and ((i % 15) == 14 or i == x - 1):
                            try:
                                await inter.author.send(embed=self.bot.util.embed(title="{} **Guild War {}**".format(self.bot.emote.get('gw'), gwnum), fields=fields, inline=True, color=self.color))
                            except:
                                await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="I can't send you the full list by private messages", color=self.color))
                                raise Exception("Returning")
                            fields = []

                if all:
                    await inter.edit_original_message("Done, please check your private messages", ephemeral=True)
                    raise Exception("Returning")
                elif type and len(result) > 6: desc = "6/{} random result(s) shown".format(len(result)) # crew
                elif not type and len(result) > 30: desc = "30/{} random result(s) shown".format(len(result)) # player
                else: desc = ""
                await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War {}**".format(self.bot.emote.get('gw'), gwnum), description=desc, fields=fields, inline=True, color=self.color))
            except Exception as e:
                if str(e) != "Returning":
                    await self.bot.sendError('findranking (search: {})'.format(terms), e)
        try: await self.bot.util.clean(inter, 45)
        except: pass

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(10, commands.BucketType.default)
    async def findgw(self, inter, what : str = commands.Param(description="crew or player", default="crew", autocomplete=["crew", "player"]), terms : str = commands.Param(description="Search value. Add %past for past GW and %id for an ID search")):
        """Search a crew or player GW score in the bot data"""
        await self.findranking(inter, (what.lower() == "crew"), terms)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def gwhelp(self, inter, what : str = commands.Param(description="Type of Value", autcomplete=['box', 'token', 'honor', 'meat']), value : str = commands.Param(description="Value to convert (support B, M and K)")):
        """Convert Guild War boxes, tokens, honors, or meats"""
        match what.lower():
            case 'token':
                try:
                    tok = self.bot.util.strToInt(value)
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
                    await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War Token Calculator ▫️ {} tokens".format(self.bot.emote.get('gw'), t), description="**{:,}** box(s) and **{:,}** leftover tokens\n**{:,}** EX (**{:,}** pots)\n**{:,}** EX+ (**{:,}** pots)\n**{:,}** NM90 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM95 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM150 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 join (**{:}** BP)".format(b, tok, ex, math.ceil(ex*30/75), explus, math.ceil(explus*30/75), n90, math.ceil(n90*30/75), n90*5, n95, math.ceil(n95*40/75), n95*10, n100, math.ceil(n100*50/75), n100*20, n150, math.ceil(n150*50/75), n150*20, wanpan, wanpan*3), color=self.color), ephemeral=True)
                except:
                    await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid token number", color=self.color), ephemeral=True)
            case 'box':
                t = 0
                box = self.bot.util.strToInt(value)
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
                await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War Token Calculator ▫️ {} boxes".format(self.bot.emote.get('gw'), b), description="**{:,}** tokens needed\n\n**{:,}** EX (**{:,}** pots)\n**{:,}** EX+ (**{:,}** pots)\n**{:,}** NM90 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM95 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM150 (**{:,}** pots, **{:,}** meats)\n**{:,}** NM100 join (**{:}** BP)".format(t, ex, math.ceil(ex*30/75), explus, math.ceil(explus*30/75), n90, math.ceil(n90*30/75), n90*5, n95, math.ceil(n95*40/75), n95*10, n100, math.ceil(n100*50/75), n100*20, n150, math.ceil(n150*50/75), n150*20, wanpan, wanpan*3), color=self.color), ephemeral=True)
            case 'meat':
                try:
                    meat = self.bot.util.strToInt(value)
                    if meat < 5 or meat > 100000: raise Exception()
                    nm90 = meat // 5
                    nm95 = meat // 10
                    nm100 = meat // 20
                    nm150 = meat // 20
                    await inter.response.send_message(embed=self.bot.util.embed(title="{} Meat Calculator ▫️ {} meats".format(self.bot.emote.get('gw'), meat), description="**{:,}** NM90 or **{:}** honors\n**{:,}** NM95 or **{:}** honors\n**{:}** NM100 or **{:}** honors\n**{:,}** NM150 or **{:}** honors\n".format(nm90, self.bot.util.valToStr(nm90*260000), nm95, self.bot.util.valToStr(nm95*910000), nm100, self.bot.util.valToStr(nm100*2650000), nm150, self.bot.util.valToStr(nm150*4100000)), color=self.color), ephemeral=True)
                except:
                    await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid meat number", color=self.color), ephemeral=True)
            case 'honor':
                try:
                    target = self.bot.util.strToInt(value)
                    if target < 10000: raise Exception()
                    exp = math.ceil(target / 80800)
                    nm90 = math.ceil(target / 260000)
                    nm95 = math.ceil(target / 910000)
                    nm100 = math.ceil(target / 2650000)
                    nm150 = math.ceil(target / 4100000)
                    await inter.response.send_message(embed=self.bot.util.embed(title="{} Honor Calculator ▫️ {} honors".format(self.bot.emote.get('gw'), self.bot.util.valToStr(target)), description="**{:,}** EX+ (**{:,}** AP)\n**{:,}** NM90 (**{:,}** AP, **{:,}** meats)\n**{:,}** NM95 (**{:,}** AP, **{:,}** meats)\n**{:,}** NM100 (**{:,}** AP, **{:,}** meats)\n**{:,}** NM150 (**{:,}** AP, **{:,}** meats)\n".format(exp, exp * 30, nm90, nm90 * 30, nm90 * 5, nm95, nm95 * 40, nm95 * 10, nm100, nm100 * 50, nm90 * 20, nm150, nm150 * 50, nm150* 20), color=self.color), ephemeral=True)
                except:
                    await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid honor number", color=self.color), ephemeral=True)
            case _:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid value type `{}`".format(what), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def honorplanning(self, inter, target : str = commands.Param(description="Number of honors (support B, M and K)")):
        """Calculate how many NM95 and 150 you need for your targeted honor"""
        try:
            target = self.bot.util.strToInt(target)
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

            await inter.response.send_message(embed=self.bot.util.embed(title="{} Honor Planning ▫️ {} honors".format(self.bot.emote.get('gw'), self.bot.util.valToStr(target)), description="Preliminaries & Interlude ▫️ **{:,}** meats (around **{:,}** EX+ and **{:}** honors)\nDay 1 and 2 total ▫️ **{:,}** NM95 (**{:}** honors)\nDay 3 and 4 total ▫️ **{:,}** NM150 (**{:}** honors)".format(math.ceil(total_meat*2), ex*2, self.bot.util.valToStr(honor[0]*2), nm[0]*2, self.bot.util.valToStr(honor[1]*2), nm[1]*2, self.bot.util.valToStr(honor[2]*2)), footer="Assuming {} meats / EX+ on average".format(meat_per_ex_average), color=self.color), ephemeral=True)
        except:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid honor number", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def gwspeed(self, inter, params : str = commands.Param(description="Leave empty to see the guide", default="")):
        """Compare multiple GW fights based on your speed"""
        try:
            if params == "": raise Exception()
            params = params.lower()
            fightdata = {'ex':[30, 3, 51000, 56], 'ex+':[30, 4, 80800, 66], 'nm90':[30, -5, 260000, 83], 'nm95':[40, -10, 910000, 111], 'nm100':[50, -20, 2650000, 168], 'nm150':[50, -20, 4100000, 257]}
            fights = params.split(' ')
            msg = ""
            for f in fights:
                if f != '':
                    elems = f.split('=')
                    if len(elems) != 2: raise Exception("Invalid string `{}`".format(f))
                    elif elems[0] not in fightdata: raise Exception("Invalid fight name `{}`".format(elems[0]))
                    time = elems[1].split(":")
                    if len(time) == 1:
                        try: time = int(time[0])
                        except: raise Exception("Invalid time `{}`".format(elems[1]))
                    elif len(time) == 2:
                        try:
                            time = int(time[0]) * 60 + int(time[1])
                        except: raise Exception("Invalid time `{}`".format(elems[1]))
                    if time <= 0: raise Exception()
                    mod = (3600 / time)
                    compare = [self.bot.util.valToStr(mod*i) for i in fightdata[elems[0]]]
                    msg += "**{}** ▫️ **{}** \▫️ **{}** AP \▫️ **{}** Token \▫️ **{}** Meat".format(elems[0].upper(), compare[2], compare[0], compare[3], compare[1])
                    msg += "\n"
            if msg == '': raise Exception()
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Speed Comparator".format(self.bot.emote.get('gw')), description="**Per hour**\n" + msg, color=self.color), ephemeral=True)
        except Exception as e:
            if str(e) != "": msg = "\nException: {}".format(e)
            else: msg = ""
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Speed Comparator Error".format(self.bot.emote.get('gw')), description="**Usage:**\nPut a list of the fight you want to compare with your speed.\nExample:\n`/gwspeed ex+=5 90=20 95=2:00`\nOnly put space between each fight, not in the formulas.\n{}".format(msg), color=self.color), ephemeral=True)

    """getCrewSummary()
    Get a GBF crew summary (what you see on the main page of a crew)
    
    Parameters
    ----------
    id: Crew id
    
    Returns
    --------
    dict: Crew data, None if error
    """
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

    """getCrewData()
    Get a GBF crew data, including its player list if public
    
    Parameters
    ----------
    target: String, can be a crew id or a crew name registered in config.json
    mode: Integer: 0=all, 1=main page data only, 2=main page and summary | add 10 to skip the cache check
    
    Returns
    --------
    dict: Crew data, None if error
    """
    def getCrewData(self, target, mode=0):
        if not self.bot.gbf.isAvailable(): # check for maintenance
            return {'error':'Game is in maintenance'}
        match target:
            case list() | tuple(): id = " ".join(target)
            case int(): id = str(target)
            case _: id = target
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
                match get:
                    case "Maintenance":
                        return {'error':'Maintenance'}
                    case "Down":
                        return {'error':'Unavailable'}
                if get is None:
                    if i == 0: # if error on page 0, the crew doesn't exist
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
                        crew['name'] = html.unescape(get['guild_name'])
                        crew['rank'] = get['guild_rank']
                        crew['ship'] = "http://game-a.granbluefantasy.jp/assets_en/img/sp/guild/thumb/top/{}.png".format(get['ship_img'])
                        crew['ship_element'] = {"10001":"wind", "20001":"fire", "30001":"water", "40001":"earth", "50001":"light", "60001":"dark"}.get(get['ship_img'].split('_')[0], 'gw')
                        crew['leader'] = html.unescape(get['leader_name'])
                        crew['leader_id'] = get['leader_user_id']
                        crew['donator'] = html.unescape(get['most_donated_name'])
                        crew['donator_id'] = get['most_donated_id']
                        crew['donator_amount'] = get['most_donated_lupi']
                        crew['message'] = html.unescape(get['introduction'])
                    else:
                        if 'player' not in crew: crew['player'] = []
                        for p in get['list']:
                            crew['player'].append({'id':p['id'], 'name':html.unescape(p['name']), 'level':p['level'], 'is_leader':p['is_leader'], 'member_position':p['member_position'], 'honor':None}) # honor is a placeholder
            
            if mode == 1: return crew
            data = self.getCrewSummary(id)
            if data is not None:
                crew = {**crew, **data}
            if mode > 0: return crew
            if not crew['private']: self.crewcache[id] = crew # only cache public crews

        # get the last gw score
        crew['scores'] = []
        data = self.bot.ranking.searchGWDB(id, 12)
        for n in range(0, 2):
            try:
                if data[n][0].ranking is None or data[n][0].day != 4:
                    crew['scores'].append("{} GW**{}** ▫️ {} ▫️ **{:,}** honors ".format(self.bot.emote.get('gw'), data[n][0].gw, ('Total Day {}'.format(data[n][0].day) if data[n][0].day > 0 else 'Total Prelim.'), data[n][0].current))
                else:
                    crew['scores'].append("{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors ".format(self.bot.emote.get('gw'), data[n][0].gw, data[n][0].ranking, data[n][0].current))
            except:
                pass

        return crew

    """processCrewData()
    Process the crew data into strings for a disnake.Embed
    
    Parameters
    ----------
    crew: Crew data
    mode: Integer (0 = auto, 1 = player ranks, 2 = player GW contributions)
    
    Returns
    --------
    tuple: Containing:
        - title: Embed title (Crew name, number of player, average rank, number online)
        - description: Embed description (Crew message, Crew leaders, GW contributions)
        - fields: Embed fields (Player list)
        - footer: Embed footer (message indicating the crew is in cache, only for public crew)
    """
    def processCrewData(self, crew, mode=0):
        # embed initialization
        title = "\u202d{} **{}**".format(self.bot.emote.get(crew['ship_element']), self.bot.util.shortenName(crew['name']))
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
            footer = "Public crew member lists are updated at least once per day"
            # get GW data
            match mode:
                case 2: gwstate = True
                case 1: gwstate = False
                case _: gwstate = self.isGWRunning()
            players = crew['player'].copy()
            gwid = None
            if gwstate:
                total = 0
                unranked = 0
                median = []
                for i in range(0, len(players)):
                    # retrieve player honors
                    honor = self.bot.ranking.searchGWDB(players[i]['id'], 2)
                    if honor is None or honor[1] is None or len(honor[1]) == 0 or honor[1][0].ranking is None:
                        players[i]['honor'] = None
                        unranked += 1
                        median.append(0)
                    else:
                        if gwid is None: gwid = honor[1][0].gw
                        players[i]['honor'] = honor[1][0].current
                        total += honor[1][0].current
                        median.append(honor[1][0].current)
                    if i > 0 and players[i]['honor'] is not None:
                        # sorting
                        for j in range(0, i):
                            if players[j]['honor'] is None or players[i]['honor'] > players[j]['honor']:
                                tmp = players[j]
                                players[j] = players[i]
                                players[i] = tmp
                if gwid and len(players) - unranked > 0:
                    average = total // (len(players) - unranked)
                    median = statistics.median(median)
                    if median > average * 1.1: health = ':sparkling_heart:'
                    elif median > average * 0.95: health = ':heart:'
                    elif median > average * 0.75: health = ':mending_heart:'
                    elif median > average * 0.5: health = ':warning:'
                    elif median > average * 0.25: health = ':put_litter_in_its_place:'
                    else: health = ':skull_crossbones:'
                    description += "\n{} GW**{}** \▫️ Player Sum **{}** \▫️ Avg. **{}**".format(health, gwid, self.bot.util.valToStr(total), self.bot.util.valToStr(average))
                    if median > 0:
                        description += " \▫️ Med. **{}**".format(self.bot.util.valToStr(median))
                    if unranked > 0:
                        description += " \▫️ **{}** n/a".format(unranked)
            # create the fields
            i = 0
            for p in players:
                if i % 10 == 0: fields.append({'name':'Page {}'.format(self.bot.emote.get('{}'.format(len(fields)+1))), 'value':''})
                i += 1
                match p['member_position']:
                    case "1": r = "captain"
                    case "2": r = "foace"
                    case "3": r = "atkace"
                    case "4": r = "deface"
                    case _: r = "ensign"
                entry = '{} [{}](http://game.granbluefantasy.jp/#profile/{})'.format(self.bot.emote.get(r), self.escape(self.bot.util.shortenName(p['name'])), p['id'])
                if gwstate:  entry += " \▫️ {}".format(self.bot.util.valToStr(p['honor']))
                else: entry += " \▫️ r**{}**".format(p['level'])
                entry += "\n"
                fields[-1]['value'] += entry
        return title, description, fields, footer

    """postCrewData()
    Call getCrewData() and processCrewData() and post the result
    
    Raises
    ------
    Exception: The raised Exception if an error occurs
    
    Parameters
    ----------
    inter: Command interaction
    id: Crew id
    mode: processCrewData() mode
    """
    async def postCrewData(self, inter, id, mode = 0):
        try:
            # retrieve formatted crew data
            await inter.response.defer()
            crew = await self.bot.do(self.getCrewData, id, 0)

            if 'error' in crew: # print the error if any
                if len(crew['error']) > 0:
                    await inter.edit_original_message(embed=self.bot.util.embed(title="Crew Error", description=crew['error'], color=self.color))
                return

            title, description, fields, footer = await self.bot.do(self.processCrewData, crew, mode)

            await inter.edit_original_message(embed=self.bot.util.embed(title=title, description=description, fields=fields, inline=True, url="http://game.granbluefantasy.jp/#guild/detail/{}".format(crew['id']), footer=footer, timestamp=crew['timestamp'], color=self.color))
            await self.bot.util.clean(inter, 60)
        except Exception as e:
            raise Exception('Error in postCrewData()') from e

    @commands.slash_command(default_permission=True)
    @commands.cooldown(2, 20, commands.BucketType.guild)
    @commands.max_concurrency(5, commands.BucketType.default)
    async def crew(self, inter, id : str = commands.Param(description="Crew ID"), mode : int = commands.Param(description="Mode (0=Auto, 1=Rank, 2=Honor)", ge=0, le=2, default=0)):
        """Get a crew profile"""
        await self.postCrewData(inter, id, mode)

    """_sortMembers()
    Sort members by GW contributions
    
    Parameters
    ------
    members: List of members
    
    Returns
    ----------
    list: Sorted list
    """
    def _sortMembers(self, members):
        for i in range(0, len(members)-1):
            for j in range(i, len(members)):
                if int(members[i][2]) < int(members[j][2]):
                    tmp = members[i]
                    members[i] = members[j]
                    members[j] = tmp
        return members

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 200, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.default)
    async def supercrew(self, inter):
        """Sort and post the top 30 server members per contribution"""
        members = []
        gwid = None
        await inter.response.defer()
        for sid in self.bot.data.save['gbfids']:
            m = inter.guild.get_or_fetch_member(int(sid))
            if m is not None:
                pdata = await self.bot.do(self.bot.ranking.searchGWDB, self.bot.data.save['gbfids'][sid], 2)
                if pdata is not None and pdata[1] is not None and len(pdata[1]) == 1:
                    if gwid is None: gwid = pdata[1][0].gw
                    members.append([pdata[1][0].id, pdata[1][0].name, pdata[1][0].current]) # id, name, honor
        if len(members) == 0:
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} Top 30 of {}".format(self.bot.emote.get('gw'), inter.guild.name), description="Unavailable", inline=True, thumbnail=inter.guild.icon.url, color=self.color))
            return
        members = await self.bot.do(self._sortMembers, members)
        fields = []
        total = 0
        for i in range(0, min(30, len(members))):
            if i % 10 == 0:
                fields.append({'name':'{}'.format(self.bot.emote.get(str(len(fields)+1))), 'value':''})
            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{}) \▫️ **{}**\n".format(members[i][1], members[i][0], self.bot.util.valToStr(members[i][2]))
            total += members[i][2]
        if gwid is None: gwid = ""
        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"Top 30 of {}".format(inter.guild.name), 'icon_url':inter.guild.icon.url}, description="{} GW**{}** ▫️ Player Total **{}** ▫️ Average **{}**".format(self.bot.emote.get('question'), gwid, self.bot.util.valToStr(total), self.bot.util.valToStr(total // min(30, len(members)))), fields=fields, inline=True, color=self.color))
        await self.bot.util.clean(inter, 60)

    """getCrewLeaders()
    Get the /gbfg/ crew leaders from the save data.
    If it's missing or outdated, data is refreshed.
    
    Parameters
    ------
    crews: List of /gbfg/ crew IDs
    
    Returns
    ----------
    list: List of crew leader IDs
    """
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

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.default)
    async def danchoranking(self, inter):
        """Sort and post all /gbfg/ captains per contribution"""
        crews = []
        await inter.response.defer()
        for e in self.bot.data.config['granblue']['gbfgcrew']:
            if self.bot.data.config['granblue']['gbfgcrew'][e] in crews: continue
            crews.append(self.bot.data.config['granblue']['gbfgcrew'][e])
        ranking = []
        leaders = await self.bot.do(self.getCrewLeaders, crews)
        for cid in leaders:
            data = await self.bot.do(self.bot.ranking.searchGWDB, leaders[cid][2], 2)
            if data is None or data[1] is None:
                continue
            gwid = ''
            if len(data[1]) == 0:
                ranking.append([leaders[cid][0], leaders[cid][1], None])
            else:
                gwid = data[1][0].gw
                ranking.append([leaders[cid][0], leaders[cid][1], data[1][0].current])
        if len(ranking) == 0:
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} /gbfg/ Dancho Ranking".format(self.bot.emote.get('gw')), description="Unavailable", color=self.color))
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
                    fields[-1]['value'] += "{} \▫️ {} \▫️ {} \▫️ **{}**\n".format(i+1, ranking[i][1], ranking[i][0], self.bot.util.valToStr(ranking[i][2]))
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} /gbfg/ GW{} Dancho Ranking".format(self.bot.emote.get('gw'), gwid), fields=fields, inline=True, color=self.color))
        await self.bot.util.clean(inter, 60)

    """_gbfgranking()
    Get the /gbfg/ crew contribution and rank them
    
    Returns
    ----------
    tuple: Containing:
        - fields: Discord Embed fields containing the data
        - gwid: Integer GW ID
    """
    def _gbfgranking(self):
        crews = []
        for e in self.bot.data.config['granblue']['gbfgcrew']:
            if self.bot.data.config['granblue']['gbfgcrew'][e] in crews: continue
            crews.append(self.bot.data.config['granblue']['gbfgcrew'][e])
        tosort = {}
        data = self.bot.ranking.GWDBver()
        if data is None or data[1] is None:
            return None, None
        else:
            gwid = ''
            for c in crews:
                data = self.bot.ranking.searchGWDB(int(c), 12)
                if data is None or data[1] is None or len(data[1]) == 0:
                    continue
                gwid = data[1][0].gw
                if data[1][0].day != 4: tosort[c] = [c, data[1][0].name, data[1][0].current, None]
                else: tosort[c] = [c, data[1][0].name, data[1][0].current, data[1][0].ranking] # id, name, honor, rank
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
                if sorted[i][3] is None:
                    fields[-1]['value'] += "{} \▫️ {} \▫️ **{}**\n".format(i+1, sorted[i][1], self.bot.util.valToStr(sorted[i][2]))
                else:
                    fields[-1]['value'] += "#**{}** \▫️ {} \▫️ **{}**\n".format(self.bot.util.valToStr(sorted[i][3]), sorted[i][1], self.bot.util.valToStr(sorted[i][2]))
            return fields, gwid

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.max_concurrency(2, commands.BucketType.default)
    async def gbfgranking(self, inter):
        """Sort and post all /gbfg/ crew per contribution"""
        await inter.response.defer()
        fields, gwid = await self.bot.do(self._gbfgranking)
        if fields is None:
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} /gbfg/ GW Ranking".format(self.bot.emote.get('gw')), description="Unavailable", color=self.color))
        else:
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} /gbfg/ GW{} Ranking".format(self.bot.emote.get('gw'), gwid), fields=fields, inline=True, color=self.color))
        await self.bot.util.clean(inter, 60)

    """_recruit()
    Get the list of /gbfg/ crews not full, sorted by rank
    
    Returns
    ----------
    list: List of open crews
    """
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

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.default)
    async def recruit(self, inter):
        """Post all recruiting /gbfg/ crews"""
        await inter.response.defer()
        if not await self.bot.do(self.bot.gbf.isAvailable):
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} /gbfg/ recruiting crews".format(self.bot.emote.get('crew')), description="Unavailable", color=self.color))
        else:
            sortedcrew = await self.bot.do(self._recruit)
            fields = []
            if len(sortedcrew) > 20: size = 15
            elif len(sortedcrew) > 10: size = 10
            else: size = 5
            slots = 0
            for i in range(0, len(sortedcrew)):
                if i % size == 0: fields.append({'name':'{}'.format(self.bot.emote.get(str(len(fields)+1))), 'value':''})
                fields[-1]['value'] += "Rank **{}** \▫️  **{}** \▫️ **{}** slots\n".format(sortedcrew[i]['average'], sortedcrew[i]['name'], 30-sortedcrew[i]['count'])
                slots += 30-sortedcrew[i]['count']
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} /gbfg/ recruiting crews ▫️ {} slots".format(self.bot.emote.get('crew'), slots), fields=fields, inline=True, color=self.color, timestamp=self.bot.util.timestamp()))
        await self.bot.util.clean(inter, 90)

    """requestCrew()
    Get a crew page data
    
    Parameters
    ------
    id: Crew ID
    page: Crew page (0 = crew main page, 1~3 = crew member pages)
    
    Returns
    ----------
    dict: Resulting data, None if error
    """
    def requestCrew(self, id : int, page : int): # get crew data
        if page == 0: return self.bot.gbf.request("http://game.granbluefantasy.jp/guild_other/guild_info/{}?PARAMS".format(id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
        else: return self.bot.gbf.request("http://game.granbluefantasy.jp/guild_other/member_list/{}/{}?PARAMS".format(page, id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def lead(self, inter, id_crew_1 : str = commands.Param(description="A crew ID"), id_crew_2 : str = commands.Param(description="A crew ID")):
        """Search two crew current scores and compare them"""
        await inter.response.defer()
        day = self.bot.ranking.getCurrentGWDayID()
        if day is None or (day % 10) <= 1:
            await inter.edit_original_message("Unavailable", ephemeral=True)
            return
        if day >= 10: day = day % 10
        ver = None
        msg = ""
        lead = None
        crew_id_list = {**(self.bot.data.config['granblue']['gbfgcrew']), **(self.bot.data.config['granblue'].get('othercrew', {}))}
        for sid in [id_crew_1, id_crew_2]:
            if sid.lower() in crew_id_list:
                id = crew_id_list[sid.lower()]
            else:
                try: id = int(sid)
                except:
                    await inter.edit_original_message("Invalid ID `{}`".format(sid), ephemeral=True)
                    return

            data = await self.bot.do(self.bot.ranking.searchGWDB, str(id), 12)
            if data is None:
                await inter.edit_original_message("Unavailable", ephemeral=True)
                return
            else:
                if data[1] is None:
                    await inter.edit_original_message("No data available for the current GW", ephemeral=True)
                    return
                result = data[1]
                gwnum = ''
                if len(result) == 0:
                    msg += "Crew [{}](http://game.granbluefantasy.jp/#guild/detail/{}) not found\n".format(sid, id)
                    lead = -1
                else:
                    gwnum = result[0].gw
                    msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ {:,}\n".format(result[0].name, id, result[0].current_day)
                    if lead is None: lead = result[0].current_day
                    elif lead >= 0: lead = abs(lead - (result[0].current_day))
        if lead is not None and lead >= 0:
            msg += "**Difference** ▫️ {:,}\n".format(lead)
        await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War {} ▫️ Day {}**".format(self.bot.emote.get('gw'), gwnum, day - 1), description=msg, timestamp=self.bot.util.timestamp(), color=self.color))

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def youlead(self, inter, opponent : str = commands.Param(description="Opponent ID (only to set", default="")):
        """Show the current match of (You)
        (You) Server Only"""
        await inter.response.defer()
        if opponent != "":
            if not self.bot.isMod(inter):
                await inter.edit_original_message("Only moderators can set the opponent", ephemeral=True)
                return
            crew_id_list = {**(self.bot.data.config['granblue']['gbfgcrew']), **(self.bot.data.config['granblue'].get('othercrew', {}))}
            if opponent.lower() in crew_id_list:
                id = crew_id_list[opponent.lower()]
            else:
                try: id = int(opponent)
                except:
                    await inter.edit_original_message("Invalid ID `{}`".format(opponent), ephemeral=True)
                    return
            if self.bot.data.save['matchtracker'] is None or self.bot.data.save['matchtracker']['id'] != id:
                self.bot.data.save['matchtracker'] = {
                    'day':None,
                    'init':False,
                    'id':id,
                    'plot':[]
                }
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War**".format(self.bot.emote.get('gw')), description="Opponent set to id `{}`, please wait the next ranking update".format(id), color=self.color))
        else:
            if self.bot.data.save['matchtracker'] is None or not self.bot.data.save['matchtracker']['init']:
                await inter.edit_original_message("Unavailable, either wait the next ranking update or add the opponent id after the command to initialize it", ephemeral=True)
            else:
                ct = self.bot.util.JST()
                you_id = self.bot.data.config['granblue']['gbfgcrew'].get('you', None)
                d = ct - self.bot.data.save['matchtracker']['last']
                msg = "Updated: **{}** ago".format(self.bot.util.delta2str(d, 0))
                if d.seconds >= 1200 and d.seconds <= 1800: msg += " ▫ *updating*"
                msg += "\n"
                end_time = self.bot.data.save['matchtracker']['last'].replace(day=self.bot.data.save['matchtracker']['last'].day+1, hour=0, minute=0, second=0, microsecond=0)
                remaining = end_time - self.bot.data.save['matchtracker']['last']
                msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ **{:,}**".format(self.bot.data.save['matchtracker']['names'][0], you_id, self.bot.data.save['matchtracker']['scores'][0])
                lead_speed = None
                if self.bot.data.save['matchtracker']['speed'] is not None:
                    lead_speed = self.bot.data.save['matchtracker']['speed'][0]
                    if self.bot.data.save['matchtracker']['speed'][0] == self.bot.data.save['matchtracker']['top_speed'][0]:
                        msg += "\n**Speed** ▫️ **Now {}/m** ▫️ **Top {}/m** :white_check_mark:".format(self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['speed'][0]), self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['top_speed'][0]))
                    else:
                        msg += "\n**Speed** ▫ Now {}/m ▫️ Top {}/m".format(self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['speed'][0]), self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['top_speed'][0]))
                    if end_time > self.bot.data.save['matchtracker']['last']:
                        msg += "\n**Estimation** ▫ Now {} ▫️ Top {}".format(self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['scores'][0] + self.bot.data.save['matchtracker']['speed'][0] * remaining.seconds//60), self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['scores'][0] + self.bot.data.save['matchtracker']['top_speed'][0] * remaining.seconds//60))
                msg += "\n\n"
                msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ **{:,}**".format(self.bot.data.save['matchtracker']['names'][1], self.bot.data.save['matchtracker']['id'], self.bot.data.save['matchtracker']['scores'][1])
                if self.bot.data.save['matchtracker']['speed'] is not None:
                    if lead_speed is not None:
                        lead_speed -= self.bot.data.save['matchtracker']['speed'][1]
                    if self.bot.data.save['matchtracker']['speed'][1] == self.bot.data.save['matchtracker']['top_speed'][1]:
                        msg += "\n**Speed** ▫️ **Now {}/m** ▫️ **Top {}/m** :warning:".format(self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['speed'][1]), self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['top_speed'][1]))
                    else:
                        msg += "\n**Speed** ▫️ Now {}/m ▫️ Top {}/m".format(self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['speed'][1]), self.bot.util.valToStrBig(self.bot.data.save['matchtracker']['top_speed'][1]))
                    if end_time > self.bot.data.save['matchtracker']['last']:
                        current_estimation = self.bot.data.save['matchtracker']['scores'][1] + self.bot.data.save['matchtracker']['speed'][1] * remaining.seconds//60
                        top_estimation = self.bot.data.save['matchtracker']['scores'][1] + self.bot.data.save['matchtracker']['top_speed'][1] * remaining.seconds//60
                        msg += "\n**Estimation** ▫ Now {} ▫️ Top {}".format(self.bot.util.valToStrBig(current_estimation), self.bot.util.valToStrBig(top_estimation))
                else:
                    lead_speed = None
                msg += "\n\n"
                lead = self.bot.data.save['matchtracker']['scores'][0] - self.bot.data.save['matchtracker']['scores'][1]
                if lead != 0:
                    msg += "**Difference** ▫️ {:,}".format(abs(lead))
                    if lead_speed is not None and lead_speed != 0:
                        try:
                            if lead < 0: lead_speed *= -1
                            msg += " ▫ {}/m".format(self.bot.util.valToStrBig(lead_speed))
                            if lead_speed < 0:
                                minute = abs(lead) / abs(lead_speed)
                                d = self.bot.data.save['matchtracker']['last'] + timedelta(seconds=minute*60)
                                e = ct.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                                if e > d:
                                    if lead > 0: msg += "\n:warning: "
                                    else: msg += "\n:white_check_mark: "
                                    msg += "The Lead switches in **{}** at current speeds".format(self.bot.util.delta2str(d - ct))
                                elif lead > 0:
                                    if self.bot.data.save['matchtracker']['scores'][0] > top_estimation:
                                        msg += "\n:confetti_ball: Opponent can't catch up without surpassing their **top speed**"
                                    elif self.bot.data.save['matchtracker']['scores'][0] > current_estimation:
                                        msg += "\n:white_check_mark: Opponent can't catch up without increasing their **current speed**"
                                    else:
                                        msg += "\n:ok: Opponent can't catch up at **current speeds**, keep going!"
                        except:
                            pass

                await inter.edit_original_message(embed=self.bot.util.embed(title="{} **Guild War {} ▫️ Day {}**".format(self.bot.emote.get('gw'), self.bot.data.save['matchtracker']['gwid'], self.bot.data.save['matchtracker']['day']-1), description=msg, timestamp=self.bot.util.timestamp(), thumbnail=self.bot.data.save['matchtracker'].get('chart', None), color=self.color))
                await self.bot.util.clean(clean, 90)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def nm(self, inter, hp_percent : int = commands.Param(description="HP% of NM95 you want to do", default=100, le=100, ge=1)):
        """Give the dragon solo equivalent of NM95"""
        todo = (131250000 * hp_percent) // 100
        drag = {
            'fire':('Ewiyar (Solo)', 180000000),
            'water':('Wilnas (Solo)', 165000000),
            'earth':('Wamdus (Solo)', 182000000),
            'wind':('Galleon (Solo)', 196000000),
            'light': None,
            'dark':('Lu Woh (Solo)', 192000000)
        }
        msg = "To do **{}% of NM95**, you must have:\n".format(hp_percent)
        for el in drag:
            if drag[el] is None:
                msg += "{} No equivalent\n".format(self.bot.emote.get(el))
            else:
                msg += "{:} **{:.1f}% HP** remaining on {:} \n".format(self.bot.emote.get(el), 100 * ((drag[el][1] - todo) / drag[el][1]), drag[el][0])
        await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War ▫️ NM95 Simulation".format(self.bot.emote.get('gw')), description=msg, color=self.color))
        await self.bot.util.clean(inter, 90)