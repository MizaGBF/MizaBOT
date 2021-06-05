from discord.ext import commands
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# DreadBarrage Cog
# ----------------------------------------------------------------------------------------------------------------
# Commands related to Dread Barrage events
# ----------------------------------------------------------------------------------------------------------------

class DreadBarrage(commands.Cog):
    """Dread Barrage commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x0062ff

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

    def isYouModOrOwner(): # for decorators
        async def predicate(ctx):
            return (ctx.bot.isServer(ctx, 'debug_server') or (ctx.bot.isServer(ctx, 'you_server') and ctx.bot.isMod(ctx)))
        return commands.check(predicate)

    def dayCheck(self, current, day, final_day=False):
        d = day - current
        if current < day and (final_day or d >= timedelta(seconds=25200)):
            return True
        return False

    def getBarrageState(self): # return the current state of the valiant in string format (which day is on going, etc...)
        if self.bot.data.save['valiant']['state'] == True:
            current_time = self.bot.util.JST()
            if current_time < self.bot.data.save['valiant']['dates']["Day 1"]:
                d = self.bot.data.save['valiant']['dates']["Day 1"] - current_time
                return "{} Dread Barrage starts in **{}**".format(self.bot.emote.get('crew'), self.bot.util.delta2str(d, 2))
            elif current_time >= self.bot.data.save['valiant']['dates']["End"]:
                with self.bot.data.lock:
                    self.bot.data.save['valiant']['state'] = False
                    self.bot.data.save['valiant']['dates'] = {}
                    self.bot.data.pending = True
                return ""
            elif current_time > self.bot.data.save['valiant']['dates']["Day 1"]:
                it = ['End', 'Day 8', 'Day 7', 'Day 6', 'Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
                for i in range(1, len(it)):
                    if current_time > self.bot.data.save['valiant']['dates'][it[i]]:
                        msg = "{} Barrage {} is on going (Time left: **{}**)".format(self.bot.emote.get('mark_a'), it[i], self.bot.util.delta2str(self.bot.data.save['valiant']['dates'][it[i-1]] - current_time))
                        if current_time < self.bot.data.save['valiant']['dates']['New Foes'] and current_time >= self.bot.data.save['valiant']['dates']['Day 1']:
                            msg += "\n{} New foes available in **{}**".format(self.bot.emote.get('mark'), self.bot.util.delta2str(self.bot.data.save['valiant']['dates']['New Foes'] - current_time, 2))
                        else:
                            msg += "\n{} Barrage is ending in **{}**".format(self.bot.emote.get('time'), self.bot.util.delta2str(self.bot.data.save['valiant']['dates'][it[0]] - current_time, 2))
                        return msg
            else:
                return ""
        else:
            return ""

    def formatElement(self, elem):
        return "{}⚔️{}".format(self.bot.emote.get(elem), self.bot.emote.get({'fire':'wind', 'water':'fire', 'earth':'water', 'wind':'earth', 'light':'dark', 'dark':'light'}.get(elem)))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['march', 'valiant', 'dread', 'db', 'dreadbarrage'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def Barrage(self, ctx, gmt : int = 9):
        """Post the Dread Barrage schedule"""
        if self.bot.data.save['valiant']['state'] == True:
            try:
                if gmt < -12 or gmt > 14: gmt = 9
                current_time = self.bot.util.JST()
                em = self.formatElement(self.bot.data.save['valiant']['element'])
                title = "{} **Dread Barrage {}** {} **{:%a. %m/%d %H:%M} TZ**\n".format(self.bot.emote.get('crew'), self.bot.data.save['valiant']['id'], em, current_time + timedelta(seconds=3600*(gmt-9)))
                if gmt == 9: title = title.replace('TZ', 'JST')
                elif gmt == 0: title = title.replace('TZ', 'GMT')
                else: title = title.replace('TZ', 'GMT{0:+}'.format(gmt))
                description = ""
                if current_time < self.bot.data.save['valiant']['dates']["End"]:
                    if current_time < self.bot.data.save['valiant']['dates']["Day 2"]:
                        description += "▫️ Start: **{:%a. %m/%d %H:%M}**\n".format(self.bot.data.save['valiant']['dates']['Day 1'] + timedelta(seconds=3600*(gmt-9)))
                    if current_time < self.bot.data.save['valiant']['dates']["Day 4"]:
                        description += "▫️ New Foes: **{:%a. %m/%d %H:%M}**\n".format(self.bot.data.save['valiant']['dates']['New Foes'] + timedelta(seconds=3600*(gmt-9)))
                    description += "▫️ Last day: **{:%a. %m/%d %H:%M}**\n".format(self.bot.data.save['valiant']['dates']['Day 8'] + timedelta(seconds=3600*(gmt-9)))
                else:
                    await ctx.send(embed=self.bot.util.embed(title="{} **Dread Barrage**".format(self.bot.emote.get('crew')), description="Not available", color=self.color))
                    with self.bot.data.lock:
                        self.bot.data.save['valiant']['state'] = False
                        self.bot.data.save['valiant']['dates'] = {}
                        self.bot.data.pending = True
                    return
                try:
                    description += self.getBarrageState()
                except Exception as e:
                    await self.bot.sendError("getBarrageState", e)

                await ctx.send(embed=self.bot.util.embed(title=title, description=description, color=self.color))
            except Exception as e:
                await self.bot.sendError("valiant", e)
        else:
            await ctx.send(embed=self.bot.util.embed(title="{} **Dread Barrage**".format(self.bot.emote.get('crew')), description="Not available", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['fugdiddreadstart', 'fugdidvaliantstart', 'fugdiddbstart', 'valianttime', 'dreadtime', 'barragetime'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def fugdidbarragestart(self, ctx):
        """Check if Dread Barrage started"""
        try:
            d = self.getBarrageState()
            if d != "":
                em = self.formatElement(self.bot.data.save['valiant']['element'])
                await ctx.reply(embed=self.bot.util.embed(title="{} **Dread Barrage {}** {} status".format(self.bot.emote.get('crew'), self.bot.data.save['valiant']['id'], em), description=d, color=self.color))
        except Exception as e:
            await ctx.reply(embed=self.bot.util.embed(title="Error", description="I have no idea what the fuck happened", footer=str(e), color=self.color))
            await self.bot.sendError("fugdidbarragestart", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setDread', 'setDreadBarrage', 'setBarrage'])
    @isYouModOrOwner()
    async def setValiant(self, ctx, id : int, advElement : str, day : int, month : int, year : int):
        """Set the Valiant date ((You) Mod only)"""
        try:
            # stop the task
            with self.bot.data.lock:
                self.bot.data.save['valiant']['state'] = False
                self.bot.data.save['valiant']['id'] = id
                self.bot.data.save['valiant']['element'] = advElement.lower()
                # build the calendar
                self.bot.data.save['valiant']['dates'] = {}
                self.bot.data.save['valiant']['dates']["Day 1"] = datetime.utcnow().replace(year=year, month=month, day=day, hour=19, minute=0, second=0, microsecond=0)
                self.bot.data.save['valiant']['dates']["Day 2"] = self.bot.data.save['valiant']['dates']["Day 1"] + timedelta(seconds=36000)
                self.bot.data.save['valiant']['dates']["Day 3"] = self.bot.data.save['valiant']['dates']["Day 2"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["New Foes"] = self.bot.data.save['valiant']['dates']["Day 3"] + timedelta(seconds=50400)
                self.bot.data.save['valiant']['dates']["Day 4"] = self.bot.data.save['valiant']['dates']["Day 3"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 5"] = self.bot.data.save['valiant']['dates']["Day 4"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 6"] = self.bot.data.save['valiant']['dates']["Day 5"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 7"] = self.bot.data.save['valiant']['dates']["Day 6"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 8"] = self.bot.data.save['valiant']['dates']["Day 7"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["End"] = self.bot.data.save['valiant']['dates']["Day 8"] + timedelta(seconds=50400)
                # set the valiant state to true
                self.bot.data.save['valiant']['state'] = True
                self.bot.data.pending = True
            await ctx.send(embed=self.bot.util.embed(title="{} Dread Barrage Mode".format(self.bot.emote.get('gw')), description="Set to : **{:%m/%d %H:%M}**".format(self.bot.data.save['valiant']['dates']["Day 1"]), color=self.color))
        except Exception as e:
            with self.bot.data.lock:
                self.bot.data.save['valiant']['dates'] = {}
                self.bot.data.save['valiant']['buffs'] = []
                self.bot.data.save['valiant']['state'] = False
                self.bot.data.pending = True
            await ctx.send(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", footer=str(e), color=self.color))
            await self.bot.sendError('setgw', e)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['disableDread', 'disableBarrage', 'disableDreadBarrage'])
    @isYouModOrOwner()
    async def disableValiant(self, ctx):
        """Disable the Valiant mode ((You) Mod only)
        It doesn't delete the Valiant settings"""
        with self.bot.data.lock:
            self.bot.data.save['valiant']['state'] = False
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['enableDread', 'enableBarrage', 'enableDreadBarrage'])
    @isYouModOrOwner()
    async def enableValiant(self, ctx):
        """Enable the Valiant mode ((You) Mod only)"""
        if self.bot.data.save['valiant']['state'] == True:
            await ctx.send(embed=self.bot.util.embed(title="{} Dread Barrage Mode".format(self.bot.emote.get('gw')), description="Already enabled", color=self.color))
        elif len(self.bot.data.save['valiant']['dates']) == 8:
            with self.bot.data.lock:
                self.bot.data.save['valiant']['state'] = True
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="No Dread Barrage available in my memory", color=self.color))