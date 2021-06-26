import discord
from discord.ext import commands

# ----------------------------------------------------------------------------------------------------------------
# Moderation Cog
# ----------------------------------------------------------------------------------------------------------------
# Mod Commands to set the bot
# ----------------------------------------------------------------------------------------------------------------

class Moderation(commands.Cog):
    """MizaBot settings for server moderators."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x2eced1

    def isMod(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isMod(ctx)
        return commands.check(predicate)

    def isYouModOrOwner(): # for decorators
        async def predicate(ctx):
            return (ctx.bot.isServer(ctx, 'debug_server') or (ctx.bot.isServer(ctx, 'you_server') and ctx.bot.isMod(ctx)))
        return commands.check(predicate)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def joined(self, ctx, member : discord.Member):
        """Says when a member joined."""
        final_msg = await ctx.reply(embed=self.bot.util.embed(title=ctx.guild.name, description="Joined at {0.joined_at}".format(member), thumbnail=member.avatar_url, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 25)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def here(self, ctx):
        """Give informations on the current channel"""
        final_msg = await ctx.reply(embed=self.bot.util.embed(title=ctx.guild.name, description="Channel: `{}`\nID: `{}`".format(ctx.channel.name, ctx.channel.id), footer="Guild ID {}".format(ctx.guild.id), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 25)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['nitro'])
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def serverinfo(self, ctx):
        """Get informations on the current guild"""
        guild = ctx.guild
        await ctx.send(embed=self.bot.util.embed(title=guild.name + " status", description="**ID** ▫️ {}\n**Owner** ▫️ {}\n**Region** ▫️ {}\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Members** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner, guild.region, len(guild.text_channels), len(guild.voice_channels), len(guild.members), len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=guild.icon_url, timestamp=guild.created_at, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def setPrefix(self, ctx, prefix_string : str):
        """Set the prefix used on your server (Mod Only)"""
        if len(prefix_string) == 0: return
        id = str(ctx.guild.id)
        if prefix_string == '$':
            if id in self.bot.data.save['prefixes']:
                with self.bot.data.lock:
                    self.bot.data.save['prefixes'].pop(id)
                    self.bot.data.pending = True
        else:
            with self.bot.data.lock:
                self.bot.data.save['prefixes'][id] = prefix_string
                self.bot.data.pending = True
        await ctx.reply(embed=self.bot.util.embed(title=ctx.guild.name, description="Server Prefix changed to `{}`".format(prefix_string), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def delST(self, ctx):
        """Delete the ST setting of this server (Mod Only)"""
        id = str(ctx.guild.id)
        if id in self.bot.data.save['st']:
            with self.bot.data.lock:
                self.bot.data.save['st'].pop(id)
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.util.embed(title=ctx.guild.name, description="No ST set on this server\nI can't delete.", thumbnail=ctx.guild.icon_url, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def setST(self, ctx, st1 : int, st2 : int):
        """Set the two ST of this server, JST Time (Mod Only)
        Example: setST 7 23 for 7am and 11pm JST"""
        if st1 < 0 or st1 >= 24 or st2 < 0 or st2 >= 24:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="Values must be between 0 and 23 included", color=self.color))
            return
        with self.bot.data.lock:
            self.bot.data.save['st'][str(ctx.message.author.guild.id)] = [st1, st2]
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['banspark'])
    @isMod()
    async def banRoll(self, ctx, member : discord.Member):
        """Ban an user from the roll ranking (Mod Only)
        To avoid idiots with fake numbers
        The ban is across all servers and can only be lifted by the owner
        Measures might be taken against mods abusing it"""
        id = str(member.id)
        if id not in self.bot.data.save['spark'][1]:
            with self.bot.data.lock:
                self.bot.data.save['spark'][1].append(id)
                self.bot.data.pending = True
            await ctx.send(embed=self.bot.util.embed(title="{} ▫️ {}".format(member.display_name, id), description="Banned from all roll rankings by {}".format(ctx.author.display_name), thumbnail=member.avatar_url, color=self.color, footer=ctx.guild.name))
            await self.bot.send('debug', embed=self.bot.util.embed(title="{} ▫️ {}".format(member.display_name, id), description="Banned from all roll rankings by {}".format(ctx.author.display_name), thumbnail=member.avatar_url, color=self.color, footer=ctx.guild.name))
        else:
            await ctx.send(embed=self.bot.util.embed(title=member.display_name, description="Already banned", thumbnail=member.avatar_url, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def toggleFullBot(self, ctx):
        """Allow or not this channel to use all commands (Mod Only)
        It cleans game/obnoxious commands outside of the whitelisted channels"""
        gid = str(ctx.guild.id)
        cid = ctx.channel.id
        with self.bot.data.lock:
            if gid not in self.bot.data.save['permitted']:
                self.bot.data.save['permitted'][gid] = []
            for i in range(0, len(self.bot.data.save['permitted'][gid])):
                if self.bot.data.save['permitted'][gid][i] == cid:
                    self.bot.data.save['permitted'][gid].pop(i)
                    self.bot.data.pending = True
                    try:
                        await self.bot.callCommand(ctx, 'seeBotPermission')
                    except:
                        pass
                    await self.bot.util.react(ctx.message, '➖')
                    return
            self.bot.data.save['permitted'][gid].append(cid)
            self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '➕')
            try:
                await self.bot.callCommand(ctx, 'seeBotPermission')
            except:
                pass

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def allowBotEverywhere(self, ctx):
        """Allow full bot access in every channel (Mod Only)"""
        gid = str(ctx.guild.id)
        if gid in self.bot.data.save['permitted']:
            with self.bot.data.lock:
                self.bot.data.save['permitted'].pop(gid)
                self.bot.data.pending = True
            await ctx.send(embed=self.bot.util.embed(title="Commands are now sauthorized everywhere", thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))
        else:
            await ctx.send(embed=self.bot.util.embed(title="Commands are already sauthorized everywhere", thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def seeBotPermission(self, ctx):
        """See all channels permitted to use all commands (Mod Only)"""
        gid = str(ctx.guild.id)
        if gid in self.bot.data.save['permitted']:
            msg = ""
            for c in ctx.guild.channels:
                if c.id in self.bot.data.save['permitted'][gid]:
                    try:
                        msg += c.name + "\n"
                    except:
                        pass
            await ctx.send(embed=self.bot.util.embed(title="Channels permitted to use all commands", description=msg, thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))
        else:
            await ctx.send(embed=self.bot.util.embed(title="Commands are sauthorized everywhere", thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def enablePinboard(self, ctx, *, expression : str = ""):
        """Enable the pinboard on your server (Mod Only)
        Use the command alone for a detailed help"""
        if expression == "":
            msg = await ctx.send(embed=self.bot.util.embed(title="How to setup the pinboard", description="Usage:\n`{}enablePinboard tracked_channel_ids reaction_emote mod_bypass threshold output_channel_id`\n\n`tracked_channel_ids`: List of channel IDs to track, separated by semicolons (example: `339155308767215618;406013959049707521`)\n`reaction_emote`: The emote used in reaction to trigger the pin\n`mod_bypass`: It must be True or False. If True, a moderator reacting will automatically trigger the pin\n`threshold`: Number of reactions needed to trigger the pin\n`output_channel_id`: The channel ID where the pins will be displayed (example: `593488798365646882`)".format(ctx.message.content[0]), color=self.color))
        else:
            args = expression.replace('  ', ' ').replace('  ', ' ').replace('  ', ' ').split(' ')
            if len(args) > 5:
                msg = await ctx.send(embed=self.bot.util.embed(title="Pinboard Error", description="**Too many parameters**\nWhat I see:\n`tracked_channel_ids={}`\n`reaction_emote={}`\n`mod_bypass={}`\n`threshold={}`\n`output_channel_id={}`".format(args[0], args[1], args[2], args[3], args[4]), footer="Did you put one extra space somewhere?", color=self.color))
            elif len(args) < 5:
                msg = await ctx.send(embed=self.bot.util.embed(title="Pinboard Error", description="**Missing parameters**", footer="Try the command without parameters to see the detailed instructions", color=self.color))
            else:
                try:
                    tracked = args[0].split(";")
                    for cid in tracked:
                        try:
                            if ctx.guild.get_channel(int(cid)) is None:
                                raise Exception()
                        except:
                            raise Exception("`{}` isn't a valid channel id".format(cid))
                    tracked = [int(cid) for cid in tracked]
                    emoji = args[1]
                    if args[2].lower() in  ['true', '1']:
                        mod = True
                    elif args[2].lower() in  ['false', '0']:
                        mod = False
                    else:
                        raise Exception("`mod_bypass={}` isn't a boolean, it should be True or False".format(args[2]))
                    try:
                        threshold = int(args[3])
                        if threshold < 1:
                            raise Exception()
                    except:
                        raise Exception("`threshold={}` is invalid, it should be a positive non null number".format(args[3]))
                    try:
                        if ctx.guild.get_channel(int(args[4])) is None:
                            raise Exception()
                        output = int(args[4])
                    except:
                        raise Exception("`output_channel_id={}` isn't a valid channel id".format(args[4]))
                    self.bot.pinboard.add(str(ctx.guild.id), tracked, emoji, mod, threshold, output)
                    msg = await ctx.send(embed=self.bot.util.embed(title="Pinboard enabled on {}".format(ctx.guild.name), description="{} tracked channels\n{} {} emotes are needed to trigger a pin\n[Output channel](https://discord.com/channels/{}/{})".format(len(tracked), threshold, emoji, ctx.guild.id, output), footer="Use the command again to change the settings", color=self.color))
                except Exception as e:
                    msg = await ctx.send(embed=self.bot.util.embed(title="Pinboard Error", description="{}".format(e), footer="Try the command without parameters to see the detailed instructions", color=self.color))
        await self.bot.util.clean(ctx, msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def disablePinboard(self, ctx):
        """Disable the pinboard on your server (Mod Only)"""
        self.bot.pinboard.remove(str(ctx.guild.id))
        await self.bot.util.react(ctx.message, '✅') # white check mark