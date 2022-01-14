import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
import math

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

    """getBarrageState()
    Return the state of the Dread Barrage event
    
    Returns
    --------
    str: Dread Barrage state
    """
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

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def db(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @db.sub_command()
    async def time(self, inter: disnake.GuildCommandInteraction, gmt : int = commands.Param(description='Your timezone from GMT', ge=-12, le=14, default=9, autocomplete=[-12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])):
        """Post the Dread Barrage schedule"""
        if self.bot.data.save['valiant']['state'] == True:
            try:
                current_time = self.bot.util.JST()
                em = self.bot.util.formatElement(self.bot.data.save['valiant']['element'])
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
                    await inter.response.send_message(embed=self.bot.util.embed(title="{} **Dread Barrage**".format(self.bot.emote.get('crew')), description="Not available", color=self.color))
                    with self.bot.data.lock:
                        self.bot.data.save['valiant']['state'] = False
                        self.bot.data.save['valiant']['dates'] = {}
                        self.bot.data.pending = True
                    await self.bot.util.clean(inter, 40)
                    return
                try:
                    description += self.getBarrageState()
                except Exception as e:
                    await self.bot.sendError("getBarrageState", e)

                await inter.response.send_message(embed=self.bot.util.embed(title=title, description=description, color=self.color))
            except Exception as e:
                await self.bot.sendError("valiant", e)
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="{} **Dread Barrage**".format(self.bot.emote.get('crew')), description="Not available", color=self.color))
            await self.bot.util.clean(inter, 40)

    @db.sub_command()
    async def token(self, inter: disnake.GuildCommandInteraction, value : str = commands.Param(description="Value to convert (support B, M and K)")):
        """Convert Dread Barrage token values"""
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
            while b < 20 and tok >= 2000:
                tok -= 2000
                b += 1
            while b < 40 and tok >= 10000:
                tok -= 10000
                b += 1
            while tok >= 15000:
                tok -= 15000
                b += 1
            s1 = math.ceil(t / 52.0)
            s2 = math.ceil(t / 70.0)
            s3 = math.ceil(t / 97.0)
            s4 = math.ceil(t / 146.0)
            s5 = math.ceil(t / 243.0)
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Dread Barrage Token Calculator ▫️ {} tokens".format(self.bot.emote.get('crew'), t), description="**{:,}** box(s) and **{:,}** leftover tokens\n**{:,}** \⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐\⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐\⭐\⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐\⭐\⭐\⭐ (**{:,}** pots)".format(b, tok, s1, math.ceil(s1*30/75), s2, math.ceil(s2*30/75), s3, math.ceil(s3*40/75), s4, math.ceil(s4*50/75), s5, math.ceil(s5*50/75)), color=self.color), ephemeral=True)
        except:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid token number", color=self.color), ephemeral=True)

    @db.sub_command()
    async def box(self, inter: disnake.GuildCommandInteraction, value : str = commands.Param(description="Value to convert (support B, M and K)")):
        """Convert Dread Barrage box values"""
        t = 0
        b = self.bot.util.strToInt(value)
        if box >= 1: t += 1600
        if box >= 2: t += 2400
        if box >= 3: t += 2400
        if box >= 4: t += 2400
        if box > 40:
            t += (box - 40) * 15000
            box = 40
        if box > 20:
            t += (box - 20) * 10000
            box = 20
        if box > 4:
            t += (box - 4) * 2000
        s1 = math.ceil(t / 52.0)
        s2 = math.ceil(t / 70.0)
        s3 = math.ceil(t / 97.0)
        s4 = math.ceil(t / 146.0)
        s5 = math.ceil(t / 243.0)
        await inter.response.send_message(embed=self.bot.util.embed(title="{} Dread Barrage Token Calculator ▫️ {} box".format(self.bot.emote.get('crew'), b), description="**{:,}** tokens needed\n\n**{:,}** \⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐\⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐\⭐\⭐ (**{:,}** pots)\n**{:,}** \⭐\⭐\⭐\⭐\⭐ (**{:,}** pots)".format(t, s1, math.ceil(s1*30/75), s2, math.ceil(s2*30/75), s3, math.ceil(s3*40/75), s4, math.ceil(s4*50/75), s5, math.ceil(s5*50/75)), color=self.color), ephemeral=True)