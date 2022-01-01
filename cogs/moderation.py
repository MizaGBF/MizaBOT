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
        async def predicate(inter):
            if inter.bot.isMod(inter):
                return True
            else:
                await inter.response.send_message(embed=inter.bot.util.embed(title="Error", description="You lack the permission to use this command"), ephemeral=True)
                return False
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
    async def channelinfo(self, inter: disnake.MessageCommandInteraction, message: disnake.Message):
        """Give informations on the current channel"""
        await inter.response.send_message(embed=self.bot.util.embed(title=inter.guild.name, description="Channel: `{}`\nID: `{}`".format(inter.channel.name, inter.channel.id), footer="Guild ID {}".format(inter.guild.id), color=self.color), ephemeral=True)

    @commands.message_command(default_permission=True, name="Server Info")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def serverinfo(self, inter: disnake.MessageCommandInteraction, message: disnake.Message):
        """Get informations on the current guild"""
        guild = inter.guild
        await inter.response.send_message(embed=self.bot.util.embed(title=guild.name + " status", description="**ID** ▫️ `{}`\n**Owner** ▫️ `{}`\n**Members** ▫️ {}\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner_id, guild.member_count, len(guild.text_channels), len(guild.voice_channels), len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=guild.icon.url, timestamp=guild.created_at, color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def mod(self, inter: disnake.GuildCommandInteraction):
        """Command Group (Mod Only)"""
        pass

    @mod.sub_command_group()
    async def strike(self, inter: disnake.GuildCommandInteraction):
        pass

    @strike.sub_command(name="del")
    async def delst(self, inter: disnake.GuildCommandInteraction):
        """Delete the ST setting of this server (Mod Only)"""
        id = str(inter.guild.id)
        if id in self.bot.data.save['st']:
            with self.bot.data.lock:
                self.bot.data.save['st'].pop(id)
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title=inter.guild.name, description="No ST set on this server\nI can't delete.", thumbnail=inter.guild.icon.url, color=self.color), ephemeral=True)

    @strike.sub_command(name="set")
    async def setst(self, inter: disnake.GuildCommandInteraction, st1 : int = commands.Param(description="First Strike Time (JST)", ge=0, le=23), st2 : int = commands.Param(description="Second Strike Time (JST)", ge=0, le=23)):
        """Set the two ST of this server, JST Time (Mod Only)"""
        with self.bot.data.lock:
            self.bot.data.save['st'][str(inter.guild.id)] = [st1, st2]
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)


    @mod.sub_command_group()
    async def ban(self, inter: disnake.GuildCommandInteraction):
        pass

    @ban.sub_command(name="roll")
    async def banroll(self, inter: disnake.GuildCommandInteraction, member: disnake.Member):
        """Ban an user from the roll ranking (Mod Only)"""
        self.bot.ban.set(member.id, self.bot.ban.SPARK)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success.\nMy owner has been notified.", color=self.color), ephemeral=True)
        await self.bot.send('debug', embed=self.bot.util.embed(title="{} ▫️ {}".format(member.display_name, id), description="Banned from all roll rankings by {}\nValues: `{}`".format(inter.author.display_name, self.bot.data.save['spark'][str(member.id)]), thumbnail=member.display_avatar, color=self.color, footer=inter.guild.name))

    @mod.sub_command_group()
    async def cleanup(self, inter: disnake.GuildCommandInteraction):
        pass

    """_seeCleanupSetting()
    Output the server cleanup settings
    
    Parameters
    --------
    inter: A command interaction
    """
    async def _seeCleanupSetting(self, inter: disnake.GuildCommandInteraction):
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

    @cleanup.sub_command(name="toggle")
    async def toggleautocleanup(self, inter: disnake.GuildCommandInteraction):
        """Toggle the auto-cleanup in this channel (Mod Only)"""
        gid = str(inter.guild.id)
        cid = inter.channel.id
        with self.bot.data.lock:
            if gid not in self.bot.data.save['permitted']:
                self.bot.data.save['permitted'][gid] = []
            for i, v in enumerate(self.bot.data.save['permitted'][gid]):
                if v == cid:
                    self.bot.data.save['permitted'][gid].pop(i)
                    self.bot.data.pending = True
                    await self._seeCleanupSetting(inter)
                    return
            self.bot.data.save['permitted'][gid].append(cid)
            self.bot.data.pending = True
            await self._seeCleanupSetting(inter)

    @cleanup.sub_command(name="reset")
    async def resetautocleanup(self, inter: disnake.GuildCommandInteraction):
        """Reset the auto-cleanup settings (Mod Only)"""
        gid = str(inter.guild.id)
        if gid in self.bot.data.save['permitted']:
            with self.bot.data.lock:
                self.bot.data.save['permitted'].pop(gid)
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="Auto Cleanup is disabled in all channels", thumbnail=inter.guild.icon.url, footer=inter.guild.name + " ▫️ " + str(inter.guild.id), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Auto Cleanup is already disabled in all channels", thumbnail=inter.guild.icon.url, footer=inter.guild.name + " ▫️ " + str(inter.guild.id), color=self.color), ephemeral=True)

    @cleanup.sub_command(name="see")
    async def seecleanupsetting(self, inter: disnake.GuildCommandInteraction):
        """See all channels where no clean up is performed (Mod Only)"""
        await self._seeCleanupSetting(inter)


    @mod.sub_command_group()
    async def pinboard(self, inter: disnake.GuildCommandInteraction):
        pass

    @pinboard.sub_command(name="enable")
    async def enablepinboard(self, inter: disnake.GuildCommandInteraction, tracked_channels : str = commands.Param(description="List of Channel IDs to track (separated by ;)"), emoji : str = commands.Param(description="The emoji used as a pin trigger"), threshold : int = commands.Param(description="Number of reactions needed to trigger the pin", ge=1), mod_bypass : int = commands.Param(description="If 1, a moderator can force the pin with a single reaction", ge=0, le=1), pinning_channel : str = commands.Param(description="ID of the channel where pin will be displayed")):
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

            if inter.guild.get_channel(int(pinning_channel)) is None:
                raise Exception("`{}` isn't a valid channel id".format(pinning_channel))
                
            self.bot.pinboard.add(str(inter.guild.id), tracked, emoji, mod, threshold, pinning_channel)
            await inter.response.send_message(embed=self.bot.util.embed(title="Pinboard enabled on {}".format(inter.guild.name), description="{} tracked channels (`{}`)\n{} {} emotes are needed to trigger a pin\n[Output channel](https://discord.com/channels/{}/{})".format(len(tracked), tracked, threshold, emoji, inter.guild.id, pinning_channel), footer="Use the command again to change those settings", color=self.color), ephemeral=True)
        except Exception as e:
            if str(e).find("isn't a valid channel") == -1:
                await self.bot.sendError('enablepinboard', e)
                await inter.response.send_message(embed=self.bot.util.embed(title="Pinboard Error", description="Critical Error, my owner got detailed error\nFeel free to try again, or wait for a fix if the error persists\n`{}`".format(e), footer="Try the command without parameters to see the detailed instructions", color=self.color), ephemeral=True)
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="Pinboard Error", description="{}".format(e), footer="Try the command without parameters to see the detailed instructions", color=self.color), ephemeral=True)

    @pinboard.sub_command(name="disable")
    async def disablepinboard(self, inter: disnake.GuildCommandInteraction):
        """Disable the pinboard on your server (Mod Only)"""
        self.bot.pinboard.remove(str(inter.guild.id))
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @pinboard.sub_command(name="see")
    async def seepinboard(self, inter: disnake.GuildCommandInteraction):
        """See the pinboard settings on your server"""
        settings = self.bot.pinboard.get(str(inter.guild.id))
        if settings is None:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="The pinboard isn't set on this server", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Pinboard settings on {}".format(inter.guild.name), description="{} tracked channels (`{}`)\n{} {} emotes are needed to trigger a pin\n[Output channel](https://discord.com/channels/{}/{})".format(len(settings['tracked']), settings['tracked'], settings['threshold'], settings['emoji'], inter.guild.id, settings['output']), footer="Use /mod pinboard enable again to change those settings", color=self.color), ephemeral=True)