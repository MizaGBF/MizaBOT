from disnake.ext import commands

# ----------------------------------------------------------------------------------------------------------------
# Roles Cog
# ----------------------------------------------------------------------------------------------------------------
# Self-Assignable roles
# ----------------------------------------------------------------------------------------------------------------

class Roles(commands.Cog):
    """Self assignable roles."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x17e37a

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

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def iam(self, inter, role_name : str = commands.Param(description="A role name")):
        """Add a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(inter.guild.id)
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if role_name.lower() not in roles:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Name `{}` not found in the self-assignable role list".format(role_name), color=self.color), ephemeral=True)
        else:
            id = roles[role_name.lower()]
            r = inter.guild.get_role(id)
            if r is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color), ephemeral=True)
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(role_name.lower())
                    if len(self.bot.data.save['assignablerole'][g]) == 0:
                        self.bot.data.save['assignablerole'].pop(g)
                    self.bot.data.pending = True
            else:
                try:
                    await inter.author.add_roles(r)
                    await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
                except:
                    await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Failed to assign the role.\nCheck if you have the role or contact a moderator.", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def iamnot(self, inter, role_name : str = commands.Param(description="A role name")):
        """Remove a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(inter.guild.id)
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if role_name.lower() not in roles:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Name `{}` not found in the self-assignable role list".format(role_name), color=self.color), ephemeral=True)
        else:
            id = roles[role_name.lower()]
            r = inter.guild.get_role(id)
            if r is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color), ephemeral=True)
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(role_name.lower())
                    if len(self.bot.data.save['assignablerole'][g]) == 0:
                        self.bot.data.save['assignablerole'].pop(g)
                    self.bot.data.pending = True
            else:
                try:
                    await inter.author.remove_roles(r)
                    await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
                except:
                    await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Failed to remove the role.\nCheck if you have the role or contact a moderator.", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def lsar(self, inter, page : int = commands.Param(description="List Page", ge=1, default=1)):
        """List the self-assignable roles available in this server"""
        g = str(inter.guild.id)
        if page < 1: page = 1
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if len(roles) == 0:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No self assignable roles available on this server", color=self.color), ephemeral=True)
            return
        if (page -1) >= len(roles) // 20:
            page = ((len(roles) - 1) // 20) + 1
        fields = []
        count = 0
        for k in list(roles.keys()):
            if count < (page - 1) * 20:
                count += 1
                continue
            if count >= page * 20:
                break
            if count % 10 == 0:
                fields.append({'name':'{} '.format(self.bot.emote.get(str(len(fields)+1))), 'value':'', 'inline':True})
            r = inter.guild.get_role(roles[k])
            if r is not None:
                fields[-1]['value'] += '{}\n'.format(k)
            else:
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(k)
                    self.bot.data.pending = True
            count += 1

        await inter.response.send_message(embed=self.bot.util.embed(title="Self Assignable Roles", fields=fields, footer="Page {}/{}".format(page, 1+len(roles)//20), color=self.color))
        await self.bot.util.clean(inter, 30)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def asar(self, inter, role_name : str = commands.Param(description="A role name")):
        """Add a role to the list of self-assignable roles (Mod Only)"""
        role = None
        for r in inter.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color), ephemeral=True)
            return
        id = str(inter.guild.id)
        with self.bot.data.lock:
            if id not in self.bot.data.save['assignablerole']:
                self.bot.data.save['assignablerole'][id] = {}
            if role.name.lower() in self.bot.data.save['assignablerole'][id]:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Role `{}` is already a self-assignable role.\nDid you mean `/rsar` ?".format(role_name), color=self.color), ephemeral=True)
                return
            self.bot.data.save['assignablerole'][id][role.name.lower()] = role.id
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="Role `{}` added to the self-assignable role list".format(role_name), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @isMod()
    async def rsar(self, inter, role_name : str = commands.Param(description="A role name")):
        """Remove a role from the list of self-assignable roles (Mod Only)"""
        role = None
        for r in inter.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color), ephemeral=True)
            return
        id = str(inter.guild.id)
        with self.bot.data.lock:
            if id not in self.bot.data.save['assignablerole']:
                self.bot.data.save['assignablerole'][id] = {}
            if role.name.lower() not in self.bot.data.save['assignablerole'][id]:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Role `{}` isn't a self-assignable role.\nDid you mean `/asar` ?".format(role_name), color=self.color), ephemeral=True)
                return
            self.bot.data.save['assignablerole'][id].pop(role.name.lower())
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="Role `{}` removed from the self-assignable role list".format(role_name), color=self.color), ephemeral=True)