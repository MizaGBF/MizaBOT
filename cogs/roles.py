import disnake
from disnake.ext import commands
from views.page import Page

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

    @commands.slash_command()
    @commands.default_member_permissions(send_messages=True, read_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(4, commands.BucketType.default)
    async def role(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @role.sub_command()
    async def iam(self, inter: disnake.GuildCommandInteraction, role_name : str = commands.Param(description="The self-assignable role you want to get")):
        """Add a role to you that you choose. Role must be on a list of self-assignable roles."""
        await inter.response.defer(ephemeral=True)
        g = str(inter.guild.id)
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if role_name.lower() not in roles:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Name `{}` not found in the self-assignable role list".format(role_name), color=self.color))
        else:
            id = roles[role_name.lower()]
            r = inter.guild.get_role(id)
            if r is None:
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color))
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(role_name.lower())
                    if len(self.bot.data.save['assignablerole'][g]) == 0:
                        self.bot.data.save['assignablerole'].pop(g)
                    self.bot.data.pending = True
            else:
                try:
                    await inter.author.add_roles(r)
                    await inter.edit_original_message(embed=self.bot.util.embed(title="The command ran with success", description="Role `{}` has been added to your profile".format(r), color=self.color))
                except:
                    await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Failed to assign the role.\nCheck if you have the role or contact a moderator.", color=self.color))

    @role.sub_command()
    async def iamnot(self, inter: disnake.GuildCommandInteraction, role_name : str = commands.Param(description="The self-assignable role you want to remove")):
        """Remove a role to you that you choose. Role must be on a list of self-assignable roles."""
        await inter.response.defer(ephemeral=True)
        g = str(inter.guild.id)
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if role_name.lower() not in roles:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Name `{}` not found in the self-assignable role list".format(role_name), color=self.color))
        else:
            id = roles[role_name.lower()]
            r = inter.guild.get_role(id)
            if r is None:
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color))
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(role_name.lower())
                    if len(self.bot.data.save['assignablerole'][g]) == 0:
                        self.bot.data.save['assignablerole'].pop(g)
                    self.bot.data.pending = True
            else:
                try:
                    await inter.author.remove_roles(r)
                    await inter.edit_original_message(embed=self.bot.util.embed(title="The command ran with success", description="Role `{}` has been removed from your profile".format(r), color=self.color))
                except:
                    await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Failed to remove the role.\nCheck if you have the role or contact a moderator.", color=self.color))

    @role.sub_command()
    async def list(self, inter: disnake.GuildCommandInteraction):
        """List the self-assignable roles available in this server"""
        await inter.response.defer(ephemeral=True)
        g = str(inter.guild.id)
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if len(roles) == 0:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="No self-assignable roles available on this server", color=self.color))
            return
        embeds = []
        fields = []
        count = 0
        for k in sorted(list(roles.keys())):
            if count % 10 == 0:
                fields.append({'name':'{} '.format(self.bot.emote.get(str(len(fields)+1))), 'value':'', 'inline':True})
            r = inter.guild.get_role(roles[k])
            if r is not None:
                fields[-1]['value'] += '{}\n'.format(k)
            else:
                with self.bot.data.lock: # remove invalid roles on the fly
                    self.bot.data.save['assignablerole'][g].pop(k)
                    self.bot.data.pending = True
            count += 1
            if count == 30:
                embeds.append(self.bot.util.embed(title="Self Assignable Roles", fields=fields, footer="Page {}/{}".format(len(embeds)+1, 1+len(roles)//30), color=self.color))
                fields = []
                count = 0
        if count != 0:
            embeds.append(self.bot.util.embed(title="Self Assignable Roles", fields=fields, footer="Page {}/{}".format(len(embeds)+1, 1+len(roles)//30), color=self.color))
        if len(embeds) > 1:
            view = Page(self.bot, owner_id=inter.author.id, embeds=embeds)
            await inter.edit_original_message(embed=embeds[0], view=view)
            view.message = await inter.original_message()
        else:
            await inter.edit_original_message(embed=embeds[0])

    @role.sub_command()
    async def add(self, inter: disnake.GuildCommandInteraction, role_name : str = commands.Param(description="The self-assignable role you want to add to the list")):
        """Add a role to the list of self-assignable roles (Mod Only)"""
        await inter.response.defer(ephemeral=True)
        if not self.bot.isMod(inter):
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Only moderators can make a role self-assignable", color=self.color))
            return
        role = None
        for r in inter.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color))
            return
        id = str(inter.guild.id)
        with self.bot.data.lock:
            if id not in self.bot.data.save['assignablerole']:
                self.bot.data.save['assignablerole'][id] = {}
            if role.name.lower() in self.bot.data.save['assignablerole'][id]:
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Role `{}` is already a self-assignable role.\nDid you mean `/role remove` ?".format(role_name), color=self.color))
                return
            self.bot.data.save['assignablerole'][id][role.name.lower()] = role.id
            self.bot.data.pending = True
        await inter.edit_original_message(embed=self.bot.util.embed(title="Role `{}` added to the self-assignable role list".format(role_name), color=self.color))

    @role.sub_command()
    async def remove(self, inter: disnake.GuildCommandInteraction, role_name : str = commands.Param(description="The self-assignable role you want to remove from the list")):
        """Remove a role from the list of self-assignable roles (Mod Only)"""
        await inter.response.defer(ephemeral=True)
        if not self.bot.isMod(inter):
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Only moderators can make a role self-assignable", color=self.color))
            return
        role = None
        for r in inter.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Role `{}` not found".format(role_name), color=self.color))
            return
        id = str(inter.guild.id)
        with self.bot.data.lock:
            if id not in self.bot.data.save['assignablerole']:
                self.bot.data.save['assignablerole'][id] = {}
            if role.name.lower() not in self.bot.data.save['assignablerole'][id]:
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Role `{}` isn't a self-assignable role.\nDid you mean `/role add` ?".format(role_name), color=self.color))
                return
            self.bot.data.save['assignablerole'][id].pop(role.name.lower())
            self.bot.data.pending = True
        await inter.edit_original_message(embed=self.bot.util.embed(title="Role `{}` removed from the self-assignable role list".format(role_name), color=self.color))