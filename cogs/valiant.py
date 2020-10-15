import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import json
import sqlite3
from xml.sax import saxutils as su

class DreadBarrage(commands.Cog):
    """Dread Barrage related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x215dc4

    def startTasks(self):
        pass

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

    def dayCheck(self, current, day, final_day=False):
        d = day - current
        if current < day and (final_day or d >= timedelta(seconds=25200)):
            return True
        return False

    def getBarrageState(self): # return the current state of the valiant in string format (which day is on going, etc...)
        if self.bot.valiant['state'] == True:
            current_time = self.bot.getJST()
            if current_time < self.bot.valiant['dates']["Day 1"]:
                d = self.bot.valiant['dates']["Day 1"] - current_time
                return "{} Dread Barrage starts in **{}**".format(self.bot.getEmote('crew'), self.bot.getTimedeltaStr(d, True))
            elif current_time >= self.bot.valiant['dates']["End"]:
                self.bot.valiant['state'] = False
                self.bot.valiant['dates'] = {}
                self.bot.savePending = True
                return ""
            elif current_time > self.bot.valiant['dates']["Day 1"]:
                it = ['End', 'Day 9', 'Day 8', 'Day 7', 'Day 6', 'Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
                for i in range(1, len(it)):
                    if current_time > self.bot.valiant['dates'][it[i]]:
                        if it[i] == 'Day 3' and current < self.bot.valiant['dates']['New Foes']:
                            msg = "{} Barrage {} is on going (**New foes in {}**)".format(self.bot.getEmote('mark_a'), it[i], self.bot.getTimedeltaStr(self.bot.valiant['dates']['New Foes'] - current_time))
                        else:
                            msg = "{} Barrage {} is on going (Time left: **{}**)".format(self.bot.getEmote('mark_a'), it[i], self.bot.getTimedeltaStr(self.bot.valiant['dates'][it[i-1]] - current_time))
                        msg += "\n{} Barrage is ending in **{}**".format(self.bot.getEmote('time'), self.bot.getTimedeltaStr(self.bot.valiant['dates'][it[0]] - current_time, True))
                        return msg
            else:
                return ""
        else:
            return ""

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['march', 'valiant', 'dread', 'db', 'dreadbarrage'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def Barrage(self, ctx, gmt :int = 9):
        """Post the Dread Barrage schedule"""
        if self.bot.valiant['state'] == True:
            try:
                if gmt < -12 or gmt > 14: gmt = 9
                current_time = self.bot.getJST()
                em = self.bot.getEmote(self.bot.valiant.get('element', ''))
                if em == "": em = ":white_small_square:"
                title = "{} **Dread Barrage {}** {} **{:%a. %m/%d %H:%M} TZ**\n".format(self.bot.getEmote('crew'), self.bot.valiant['id'], em, current_time + timedelta(seconds=3600*(gmt-9)))
                if gmt == 9: title = title.replace('TZ', 'JST')
                elif gmt == 0: title = title.replace('TZ', 'GMT')
                else: title = title.replace('TZ', 'GMT{0:+}'.format(gmt))
                description = ""
                if current_time < self.bot.valiant['dates']["End"]:
                    if current_time < self.bot.valiant['dates']["Day 2"]:
                        description += "▫️ Start: **{:%a. %m/%d %H:%M}**\n".format(self.bot.valiant['dates']['Day 1'] + timedelta(seconds=3600*(gmt-9)))
                    if current_time < self.bot.valiant['dates']["Day 4"]:
                        description += "▫️ New Foes: **{:%a. %m/%d %H:%M}**\n".format(self.bot.valiant['dates']['New Foes'] + timedelta(seconds=3600*(gmt-9)))
                    description += "▫️ Last day: **{:%a. %m/%d %H:%M}**\n".format(self.bot.valiant['dates']['Day 9'] + timedelta(seconds=3600*(gmt-9)))
                else:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Dread Barrage**".format(self.bot.getEmote('crew')), description="Not available", color=self.color))
                    self.bot.valiant['state'] = False
                    self.bot.valiant['dates'] = {}
                    self.bot.savePending = True
                    return
                try:
                    description += self.getBarrageState()
                except Exception as e:
                    await self.bot.sendError("getBarrageState", str(e))

                await ctx.send(embed=self.bot.buildEmbed(title=title, description=description, color=self.color))
            except Exception as e:
                await self.bot.sendError("valiant", str(e))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Dread Barrage**".format(self.bot.getEmote('crew')), description="Not available", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['fugdiddreadstart', 'fugdidvaliantstart', 'fugdiddbstart'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def fugdidbarragestart(self, ctx):
        """Check if Dread Barrage started"""
        try:
            d = self.getBarrageState()
            if d != "":
                em = self.bot.getEmote(self.bot.valiant.get('element', ''))
                if em == "": em = ":white_small_square:"
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}** {} status".format(self.bot.getEmote('crew'), self.bot.valiant['id'], em), description=d, color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("fugdidbarragestart", str(e))