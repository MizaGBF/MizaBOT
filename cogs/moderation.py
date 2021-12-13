import disnake
from disnake.ext import commands

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

    """isMod()
    Command decorator, to check if the command is used by a server moderator
    
    Returns
    --------
    command check
    """
    def isMod(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isMod(ctx)
        return commands.check(predicate)

    @commands.user_command(default_permission=True, name="Profile Picture")
    async def avatar(self, inter: disnake.UserCommandInteraction, user: disnake.User):
        """Retrieve the profile picture of an user"""
        await inter.response.send_message(user.display_avatar.url, ephemeral=True)

    @commands.user_command(default_permission=True, name="Server Join Date")
    async def joined(self, inter: disnake.UserCommandInteraction, member: disnake.Member):
        """Retrieve the date at which a member joined this server"""
        await inter.response.send_message(embed=self.bot.util.embed(author={'name':inter.author.display_name, 'icon_url':inter.author.display_avatar}, description="Joined at `{0.joined_at}`".format(member, member), color=self.color), ephemeral=True)

    @commands.message_command(default_permission=True, name="Channel Info")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def channelinfo(self, inter: disnake.MessageCommandInteraction):
        """Give informations on the current channel"""
        final_msg = await inter.response.send_message(embed=self.bot.util.embed(title=inter.guild.name, description="Channel: `{}`\nID: `{}`".format(inter.channel.name, inter.channel.id), footer="Guild ID {}".format(inter.guild.id), color=self.color), ephemeral=True)

    @commands.message_command(default_permission=True, name="Server Info")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def serverinfo(self, inter: disnake.MessageCommandInteraction):
        """Get informations on the current guild"""
        guild = inter.guild
        msg = await inter.response.send_message(embed=self.bot.util.embed(title=guild.name + " status", description="**ID** ▫️ `{}`\n**Owner** ▫️ `{}``\n**Members** ▫️ {}\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner_id, guild.member_count, len(guild.text_channels), len(guild.voice_channels), len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=guild.icon.url, timestamp=guild.created_at, color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def delst(self, inter):
        """Delete the ST setting of this server (Mod Only)"""
        id = str(inter.guild.id)
        if id in self.bot.data.save['st']:
            with self.bot.data.lock:
                self.bot.data.save['st'].pop(id)
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title=inter.guild.name, description="No ST set on this server\nI can't delete.", thumbnail=inter.guild.icon.url, color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def setst(self, inter, st1 : int = commands.Param(description="First Strike Time (JST)", ge=0, le=23), st2 : int = commands.Param(description="Second Strike Time (JST)", ge=0, le=23)):
        """Set the two ST of this server, JST Time (Mod Only)
        Example: setST 7 23 for 7am and 11pm JST"""
        with self.bot.data.lock:
            self.bot.data.save['st'][str(inter.guild.id)] = [st1, st2]
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.user_command(default_permission=True, name="Check for Bans")
    @isMod()
    async def bancheck(self, inter: disnake.UserCommandInteraction, member: disnake.Member):
        """Check if an user has a ban registered in the bot (Mod Only)"""
        msg = ""
        if self.bot.ban.check(member.id, self.bot.ban.OWNER): msg += "Banned from having the bot in its own servers\n"
        if self.bot.ban.check(member.id, self.bot.ban.SPARK): msg += "Banned from appearing in `rollRanking`\n"
        if self.bot.ban.check(member.id, self.bot.ban.PROFILE): msg += "Banned from using `setProfile`\n"
        if self.bot.ban.check(member.id, self.bot.ban.OWNER): msg += "Banned from using the bot\n"
        if msg == "": msg = "No Bans set for this user"
        msg = await inter.response.send_message(embed=self.bot.util.embed(author={'name':inter.author.display_name, 'icon_url':inter.author.display_avatar}, description=msg, color=self.color), ephemeral=True)

    """_seeCleanupSetting()
    Output the server cleanup settings
    
    Parameters
    --------
    inter: A command interaction
    """
    async def _seeCleanupSetting(self, inter):
        gid = str(inter.guild.id)
        if gid in self.bot.data.save['permitted']:
            msg = ""
            for c in inter.guild.channels:
                if c.id in self.bot.data.save['permitted'][gid]:
                    try:
                        msg += c.name + "\n"
                    except:
                        pass
            await inter.response.send_message(embed=self.bot.util.embed(title="Auto Cleanup is enable in all channels but the following ones:", description=msg, thumbnail=inter.guild.icon.url, footer=inter.guild.name + " ▫️ " + str(inter.guild.id), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Auto Cleanup is disabled in all channels", thumbnail=inter.guild.icon.url, footer=inter.guild.name + " ▫️ " + str(inter.guild.id), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def toggleautocleanup(self, inter):
        """Toggle the auto-cleanup in this channel (Mod Only)"""
        gid = str(inter.guild.id)
        cid = inter.channel.id
        with self.bot.data.lock:
            if gid not in self.bot.data.save['permitted']:
                self.bot.data.save['permitted'][gid] = []
            for i in range(0, len(self.bot.data.save['permitted'][gid])):
                if self.bot.data.save['permitted'][gid][i] == cid:
                    self.bot.data.save['permitted'][gid].pop(i)
                    self.bot.data.pending = True
                    await self._seeCleanupSetting(inter)
                    return
            self.bot.data.save['permitted'][gid].append(cid)
            self.bot.data.pending = True
            await self._seeCleanupSetting(inter)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def resetautocleanup(self, inter):
        """Reset the auto-cleanup settings (Mod Only)"""
        gid = str(inter.guild.id)
        if gid in self.bot.data.save['permitted']:
            with self.bot.data.lock:
                self.bot.data.save['permitted'].pop(gid)
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="Auto Cleanup is disabled in all channels", thumbnail=inter.guild.icon.url, footer=inter.guild.name + " ▫️ " + str(inter.guild.id), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Auto Cleanup is already disabled in all channels", thumbnail=inter.guild.icon.url, footer=inter.guild.name + " ▫️ " + str(inter.guild.id), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def seecleanupsetting(self, inter):
        """See all channels where no clean up is performed (Mod Only)"""
        await self._seeCleanupSetting(inter)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def enablepinboard(self, inter, tracked_channels : str = commands.Param(description="List of Channel IDs to track (separated by ;)"), emoji : str = commands.Param(description="The emoji used as a pin trigger"), threshold : int = commands.Param(description="Number of reactions needed to trigger the pin", ge=1), mod_bypass : int = commands.Param(description="If 1, a moderator can force the pin with a single reaction", ge=0, le=1, autocomplete=[0, 1]), pinning_channel : int = commands.Param(description="ID of the channel where pin will be displayed", ge=0)):
        """Enable the pinboard on your server (Mod Only)"""
        try:
            tracked = tracked_channels.replace(' ', '').split(';')
            for cid in tracked:
                try:
                    if inter.guild.get_channel(int(cid)) is None:
                        raise Exception()
                except:
                    raise Exception("`{}` isn't a valid channel id".format(cid))
            tracked = [int(cid) for cid in tracked] # convert to int
            
            mod = (False if mod_bypass == 0 else True)

            if inter.guild.get_channel(pinning_channel) is None:
                raise Exception("`{}` isn't a valid channel id".format(pinning_channel))
                
            self.bot.pinboard.add(str(inter.guild.id), tracked, emoji, mod, threshold, pinning_channel)
            await inter.response.send_message(embed=self.bot.util.embed(title="Pinboard enabled on {}".format(inter.guild.name), description="{} tracked channels (`{}`)\n{} {} emotes are needed to trigger a pin\n[Output channel](https://discord.com/channels/{}/{})".format(len(tracked), tracked, threshold, emoji, inter.guild.id, pinning_channel), footer="Use the command again to change those settings", color=self.color), ephemeral=True)
        except Exception as e:
            await self.bot.sendError('enablepinboard', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="Pinboard Error", description="{}".format(e), footer="Try the command without parameters to see the detailed instructions", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def disablepinboard(self, inter):
        """Disable the pinboard on your server (Mod Only)"""
        self.bot.pinboard.remove(str(inter.guild.id))
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def seepinboard(self, inter):
        """See the pinboard settings on your server"""
        settings = self.bot.pinboard.get(str(inter.guild.id))
        if settings is None:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="The pinboard isn't set on this server", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Pinboard settings on {}".format(inter.guild.name), description="{} tracked channels (`{}`)\n{} {} emotes are needed to trigger a pin\n[Output channel](https://discord.com/channels/{}/{})".format(len(settings['tracked']), settings['tracked'], settings['threshold'], settings['emoji'], inter.guild.id, settings['output']), footer="Use /enablepinboard again to change those settings", color=self.color), ephemeral=True)