import disnake
from disnake.ext import commands
import itertools
from views.poll import Poll

# ----------------------------------------------------------------------------------------------------------------
# General Cog
# ----------------------------------------------------------------------------------------------------------------
# Commands related to the current instance of MizaBOT
# ----------------------------------------------------------------------------------------------------------------

class General(commands.Cog):
    """MizaBot commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xd12e57

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 100, commands.BucketType.user)
    async def invite(self, inter: disnake.GuildCommandInteraction):
        """Get the MizaBOT invite link"""
        if 'invite' not in self.bot.data.save:
            await inter.response.send_message(embed=self.bot.util.embed(title="Invite Error", description="Invitation settings aren't set, hence the bot can't be invited.\nIf you are the server owner, check the `setInvite` command", timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)
        elif self.bot.data.save['invite']['state'] == False or len(self.bot.guilds) >= self.bot.data.save['invite']['limit']:
            await inter.response.send_message(embed=self.bot.util.embed(title="Invite Error", description="Invitations are currently closed.", timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title=inter.guild.me.name, description="{}\nCurrently only servers of 30 members or more can be added.\nMisuses of this link will result in a server-wide ban.".format(self.bot.data.config['strings']["invite()"]), thumbnail=inter.guild.me.display_avatar, timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def bug_report(self, inter: disnake.GuildCommandInteraction, report : str = commands.Param()):
        """Send a bug report (or your love confessions) to the author"""
        await self.bot.send('debug', embed=self.bot.util.embed(title="Bug Report", description=report, footer="{} ▫️ User ID: {}".format(inter.author.name, inter.author.id), thumbnail=inter.author.display_avatar, color=self.color))
        await inter.response.send_message(embed=self.bot.util.embed(title="Error", description='Thank you, your report has been sent with success.', color=self.color), ephemeral=True)

    @commands.message_command(default_permission=True, name="Report a Bug")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def bugreport(self, inter: disnake.MessageCommandInteraction):
        """Send the selected message to the author"""
        if len(inter.target.content) > 0:
            await self.bot.send('debug', embed=self.bot.util.embed(title="Bug Report", description=inter.target.content, footer="{} ▫️ User ID: {}".format(inter.author.name, inter.author.id), thumbnail=inter.author.display_avatar, color=self.color))
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description='Thank you, your report has been sent with success.', color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="This message can't be sent", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def help(self, inter: disnake.GuildCommandInteraction):
        """Post a link to the online help"""
        await inter.response.send_message(embed=self.bot.util.embed(title=self.bot.description.splitlines()[0], description="Online Help [here](https://mizagbf.github.io/MizaBOT/)\nCode source [here](https://github.com/MizaGBF/MizaBOT)", thumbnail=inter.me.display_avatar, color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def mizabot(self, inter: disnake.GuildCommandInteraction):
        """Post the bot status"""
        await inter.response.send_message(embed=self.bot.util.embed(title="{} is Ready".format(self.bot.user.display_name), description=self.bot.util.statusString(), thumbnail=self.bot.user.display_avatar, timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def changelog(self, inter: disnake.GuildCommandInteraction):
        """Post the bot changelog"""
        msg = ""
        for c in self.bot.changelog:
            msg += "▫️ {}\n".format(c)
        if msg != "":
            await inter.response.send_message(embed=self.bot.util.embed(title="{} ▫️ v{}".format(inter.me.display_name, self.bot.version), description="**Changelog**\n" + msg, thumbnail=inter.me.display_avatar, color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No Changelog available", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(5, commands.BucketType.default)
    async def poll(self, inter: disnake.GuildCommandInteraction, duration : int = commands.Param(description="In seconds", ge=60, le=500), poll_data : str = commands.Param(description="Format is: `title;choice1;choice2;...;choiceN`")):
        """Make a poll"""
        try:
            splitted = poll_data.split(';')
            if len(splitted) < 2: raise Exception('Specify at least a poll title and two choices\nFormat: `duration title;choice1;choice2;...;choiceN`')
            view = Poll(self.bot, inter.author, self.color, splitted[0], splitted[1:])
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Your poll is starting", color=self.color), ephemeral=True)
            msg_to_edit = await inter.channel.send(embed=self.bot.util.embed(author={'name':'{} started a poll'.format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, title=splitted[0], description="{} seconds remaining to vote".format(duration), color=self.color))
            msg_view = await inter.channel.send('\u200b', view=view)
            await view.run_poll(duration, msg_to_edit, inter.channel)
            await msg_view.delete()
        except Exception as e:
            try: await inter.response.send_message(embed=self.bot.util.embed(title="Poll error", description="{}".format(e), color=self.color), ephemeral=True)
            except: await inter.edit_original_message(embed=self.bot.util.embed(title="Poll error", description="{}".format(e), color=self.color))

    @commands.slash_command(default_permission=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def calc(self, inter: disnake.GuildCommandInteraction, expression : str = commands.Param(description='Mathematical Expression')):
        """Process a mathematical expression. Support variables (Example: cos(a + b) / c, a = 1, b=2,c = 3)."""
        try:
            m = expression.split(",")
            d = {}
            for i in range(1, len(m)): # process the variables if any
                x = m[i].replace(" ", "").split("=")
                if len(x) == 2: d[x[0]] = float(x[1])
                else: raise Exception('')
            msg = "`{}` = **{}**".format(m[0], self.bot.calc.evaluate(m[0], d))
            if len(d) > 0:
                msg += "\nwith:\n"
                for k in d:
                    msg += "{} = {}\n".format(k, d[k])
            await inter.response.send_message(embed=self.bot.util.embed(title="Calculator", description=msg, color=self.color))
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Error\n"+str(e), color=self.color), ephemeral=True)
        await self.bot.util.clean(inter, 60)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def jst(self, inter: disnake.GuildCommandInteraction):
        """Post the current time, JST timezone"""
        await inter.response.send_message(embed=self.bot.util.embed(title="{} {:%Y/%m/%d %H:%M} JST".format(self.bot.emote.get('clock'), self.bot.util.JST()), color=self.color), ephemeral=True)