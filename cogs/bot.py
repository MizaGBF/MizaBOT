from discord.ext import commands
import itertools

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
        """Post the link to the bot code source"""
        final_msg = await ctx.reply(embed=self.bot.util.embed(title=self.bot.description.splitlines()[0], description="Code source [here](https://github.com/MizaGBF/MizaBOT)\nCommand list available [here](https://mizagbf.github.io/MizaBOT/)", thumbnail=ctx.guild.me.avatar_url, color=self.color))
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

    # retrieve a command category
    def get_category(self, command, *, no_category=""):
        cog = command.cog
        return ('**' + cog.qualified_name + '** :white_small_square: ' + cog.description) if cog is not None else no_category

    # check command predicate
    async def predicate(self, ctx, cmd):
        try:
            return await cmd.can_run(ctx)
        except Exception:
            return False

    # smaller implementation of filter_commands() from discord.py help
    async def filter_commands(self, ctx, cmds):
        iterator = filter(lambda c: not c.hidden, cmds)

        ret = []
        for cmd in iterator:
            valid = await self.predicate(ctx, cmd)
            if valid:
                ret.append(cmd)

        ret.sort(key=self.get_category)
        return ret

    # implementation of get_command_signature() from discord.py help
    def get_command_signature(self, ctx, command):
        parent = command.parent
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + ' ' + parent.signature)
            parent = parent.parent
        parent_sig = ' '.join(reversed(entries))

        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'[{command.name}|{aliases}]'
            if parent_sig:
                fmt = parent_sig + ' ' + fmt
            alias = fmt
        else:
            alias = command.name if not parent_sig else parent_sig + ' ' + command.name

        return f'{self.bot.prefix(None, ctx.message)}{alias} {command.signature}' #todo: replace prefix by ctx.clean_prefix

    # search the bot categories and help
    async def search_help(self, ctx, terms):
        flags = []
        t = terms.lower()
        # searching category match
        for key in self.bot.cogs:
            if t == self.bot.cogs[key].qualified_name.lower():
                return [[0, self.bot.cogs[key]]]
            elif t in self.bot.cogs[key].qualified_name.lower():
                flags.append([0, self.bot.cogs[key]])
            elif t in self.bot.cogs[key].description.lower():
                flags.append([0, self.bot.cogs[key]])
        # searching command match
        for cmd in self.bot.commands:
            if not await self.predicate(ctx, cmd):
                continue
            if t == cmd.name.lower():
                return [[1, cmd]]
            elif t in cmd.name.lower() or t in cmd.help.lower():
                flags.append([1, cmd])
            else:
                for al in cmd.aliases:
                    if t == al.lower() or t in al.lower():
                        flags.append([1, cmd])
        return flags

    # send the cog detailed help to the user via DM
    async def get_cog_help(self, ctx, cog):
        try:
            await self.bot.util.react(ctx.message, '📬')
        except:
            return await ctx.reply(embed=self.bot.util.embed(title="Help Error", description="Unblock me to receive the Help"))

        filtered = await self.filter_commands(ctx, cog.get_commands()) # sort
        fields = []
        for c in filtered:
            if c.short_doc == "": fields.append({'name':"{} ▫ {}".format(c.name, self.get_command_signature(ctx, c)), 'value':"No description"})
            else: fields.append({'name':"{} ▫ {}".format(c.name, self.get_command_signature(ctx, c)), 'value':c.short_doc})
            if len(str(fields)) > 5800 or len(fields) > 24: # embeds have a 6000 and 25 fields characters limit, I send and make a new embed if needed
                try:
                    await ctx.author.send(embed=self.bot.util.embed(title="{} **{}** Category".format(self.bot.emote.get('mark'), cog.qualified_name), description=cog.description, fields=fields, color=cog.color)) # author.send = dm
                    fields = []
                except:
                    msg = await ctx.reply(embed=self.bot.util.embed(title="Help Error", description="I can't send you a direct message"))
                    await self.bot.util.unreact(ctx.message, '📬')
                    return msg
        if len(fields) > 0:
            try:
                await ctx.author.send(embed=self.bot.util.embed(title="{} **{}** Category".format(self.bot.emote.get('mark'), cog.qualified_name), description=cog.description, fields=fields, color=cog.color)) # author.send = dm
            except:
                msg = await ctx.reply(embed=self.bot.util.embed(title="Help Error", description="I can't send you a direct message"))
                await self.bot.util.unreact(ctx.message, '📬')
                return msg

        await self.bot.util.unreact(ctx.message, '📬')
        return None

    # print the default help when no search terms is specifieed
    async def default_help(self, ctx):
        me = ctx.author.guild.me # bot own user infos
        # get command categories
        filtered = await self.filter_commands(ctx, self.bot.commands) # sort all category and commands
        to_iterate = itertools.groupby(filtered, key=self.get_category)
        # categories to string
        cats = ""
        for category, coms in to_iterate:
            if category != "":
                cats += "{}\n".format(category)
        return await ctx.reply(embed=self.bot.util.embed(title=me.name + " Help", description=self.bot.description + "\n\nUse `{}help <command_name>` or `{}help <category_name>` to get more informations\n**Categories:**\n".format(ctx.message.content[0], ctx.message.content[0]) + cats, thumbnail=me.avatar_url, color=self.color))

    # detailed category help
    async def category_help(self, terms, ctx, cog):
        me = ctx.author.guild.me # bot own user infos
        msg = await self.get_cog_help(ctx, cog)
        if msg is None:
            msg = await ctx.reply(embed=self.bot.util.embed(title=me.name + " Help", description="Full help for `{}` has been sent via direct messages".format(terms), color=self.color))
        return msg

    # detailed command help
    async def command_help(self, terms, ctx, cmd):
        me = ctx.author.guild.me # bot own user infos
        return await ctx.reply(embed=self.bot.util.embed(title="{} **{}** Command".format(self.bot.emote.get('mark'), cmd.name), description=cmd.help, fields=[{'name':'Usage', 'value':self.get_command_signature(ctx, cmd)}], color=self.color))

    # multiple help matches
    async def multiple_help(self, terms, ctx, flags):
        me = ctx.author.guild.me # bot own user infos
        desc = "**Please specify what you are looking for**\n"
        for res in flags:
            if res[0] == 0:
                desc += "Category **{}**\n".format(res[1].qualified_name)
            elif res[0] == 1:
                desc += "Command **{}**\n".format(res[1].name)
        return await ctx.reply(embed=self.bot.util.embed(title=me.name + " Help", description=desc, thumbnail=me.avatar_url, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['command', 'commands', 'category', 'categories', 'cog', 'cogs'])
    @commands.cooldown(2, 8, commands.BucketType.user)
    async def help(self, ctx, *, terms : str = ""):
        """Get the bot help"""
        if len(terms) == 0: # no parameters
            msg = await self.default_help(ctx)
        else: # search parameter
            flags = await self.search_help(ctx, terms)
            if len(flags) == 0: # no matches
                me = ctx.author.guild.me # bot own user infos
                msg = await ctx.reply(embed=self.bot.util.embed(title=me.name + " Help", description="`{}` not found".format(terms), thumbnail=me.avatar_url, color=self.color))
            elif len(flags) == 1: # one match
                if flags[0][0] == 0: msg = await self.category_help(terms, ctx, flags[0][1])
                elif flags[0][0] == 1: msg = await self.command_help(terms, ctx, flags[0][1])
            elif len(flags) > 20: # more than 20 matches
                me = ctx.author.guild.me # bot own user infos
                msg = await ctx.reply(embed=self.bot.util.embed(title=me.name + " Help", description="Too many results, please try to be a bit more specific or use the [Online Help](https://mizagbf.github.io/MizaBOT/)", thumbnail=me.avatar_url, color=self.color))
            else: # multiple matches
                msg = await self.multiple_help(terms, ctx, flags)
        await self.bot.util.clean(ctx, msg, 60)