from discord.ext import commands

# ----------------------------------------------------------------------------------------------------------------
# Bot Cog
# ----------------------------------------------------------------------------------------------------------------
# Commands related to the current instance of MizaBOT
# ----------------------------------------------------------------------------------------------------------------

class Bot(commands.Cog):
    """MizaBot commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xd12e57

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['bug', 'report', 'bug_report'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def bugReport(self, ctx, *, terms : str):
        """Send a bug report (or your love confessions) to the author"""
        if len(terms) == 0:
            return
        await self.bot.send('debug', embed=self.bot.util.embed(title="Bug Report", description=terms, footer="{} ▫️ User ID: {}".format(ctx.author.name, ctx.author.id), thumbnail=ctx.author.avatar_url, color=self.color))
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['source'])
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def github(self, ctx):
        """Post the bot.py file running right now"""
        final_msg = await ctx.reply(embed=self.bot.util.embed(title=self.bot.description.splitlines()[0], description="Code source at https://github.com/MizaGBF/MizaBOT", thumbnail=ctx.guild.me.avatar_url, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 25)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mizabot'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def status(self, ctx):
        """Post the bot status"""
        final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} is Ready".format(self.bot.user.display_name), description=self.bot.util.statusString(), thumbnail=self.bot.user.avatar_url, timestamp=self.bot.util.timestamp(), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 40)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def changelog(self, ctx):
        """Post the bot changelog"""
        msg = ""
        for c in self.bot.changelog:
            msg += "▫️ {}\n".format(c)
        if msg != "":
            final_msg = await ctx.send(embed=self.bot.util.embed(title="{} ▫️ v{}".format(ctx.guild.me.display_name, self.bot.version), description="**Changelog**\n" + msg, thumbnail=ctx.guild.me.avatar_url, color=self.color))
            await self.bot.util.clean(ctx, final_msg, 40)