from discord.ext import commands
import itertools

# ----------------------------------------------------------------------------------------------------------------
# Help Component
# ----------------------------------------------------------------------------------------------------------------
# Custom Help Command for the bot
# Cog Command Lists are sent by direct message to the user, others are sent in reply
# This Component doesn't behave as the others (No reset on reload and no instance in the MizaBot class)
# ----------------------------------------------------------------------------------------------------------------

class Help(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__()
        self.dm_help = True # force dm only (although our own functions only send in dm, so it should be unneeded)

    async def send_error_message(self, error):
        try: await self.context.message.add_reaction('❎') # white negative mark
        except: pass

    async def send_bot_help(self, mapping): # main help command (called when you do $help). this function reuse the code from the commands.DefaultHelpCommand class
        ctx = self.context # get $help context
        bot = ctx.bot
        me = ctx.author.guild.me # bot own user infos

        no_category = ""
        def get_category(command, *, no_category=no_category): # function to retrieve the command category
            cog = command.cog
            return ('**' + cog.qualified_name + '** :white_small_square: ' + cog.description) if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category) # sort all category and commands
        to_iterate = itertools.groupby(filtered, key=get_category)

        cats = ""
        for category, coms in to_iterate:
            if category != no_category:
                cats += "{}\n".format(category)
        msg = await ctx.reply(embed=bot.util.embed(title=me.name + " Help", description=bot.description + "\n\nUse `{}help <command_name>` or `{}help <category_name>` to get more informations\n**Categories:**\n".format(ctx.message.content[0], ctx.message.content[0]) + cats, thumbnail=me.avatar_url))

        await bot.util.clean(ctx, msg, 60)

    async def send_command_help(self, command): # same thing, but for a command ($help <command>)
        ctx = self.context
        bot = ctx.bot

        # send the help
        embed = bot.util.embed(title="{} **{}** Command".format(bot.emote.get('mark'), command.name), description=command.help, fields=[{'name':'Usage', 'value':self.get_command_signature(command)}])

        msg = await ctx.reply(embed=embed) # author.send = dm

        await bot.util.clean(ctx, msg, 60)

    async def send_cog_help(self, cog): # category help ($help <category)
        ctx = self.context
        bot = ctx.bot
        try:
            await bot.util.react(ctx.message, '📬')
        except:
            await ctx.send(embed=bot.util.embed(title="Help Error", description="Unblock me to receive the Help"))
            return

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands) # sort
        fields = []
        for c in filtered:
            if c.short_doc == "": fields.append({'name':"{} ▫ {}".format(c.name, self.get_command_signature(c)), 'value':"No description"})
            else: fields.append({'name':"{} ▫ {}".format(c.name, self.get_command_signature(c)), 'value':c.short_doc})
            if len(str(fields)) > 5800 or len(fields) > 24: # embeds have a 6000 and 25 fields characters limit, I send and make a new embed if needed
                try:
                    await ctx.author.send(embed=bot.util.embed(title="{} **{}** Category".format(bot.emote.get('mark'), cog.qualified_name), description=cog.description, fields=fields, color=cog.color)) # author.send = dm
                    fields = []
                except:
                    await ctx.send(embed=bot.util.embed(title="Help Error", description="I can't send you a direct message"))
                    await bot.util.unreact(ctx.message, '📬')
                    return
        if len(fields) > 0:
            try:
                await ctx.author.send(embed=bot.util.embed(title="{} **{}** Category".format(bot.emote.get('mark'), cog.qualified_name), description=cog.description, fields=fields, color=cog.color)) # author.send = dm
            except:
                await ctx.send(embed=bot.util.embed(title="Help Error", description="I can't send you a direct message"))
                await bot.util.unreact(ctx.message, '📬')
                return

        await bot.util.unreact(ctx.message, '📬')
        await bot.util.react(ctx.message, '✅') # white check mark