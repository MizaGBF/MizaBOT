from discord.ext import commands

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

    def isMod(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isMod(ctx)
        return commands.check(predicate)

    def _roleStats(self, ctx, name):
        g = ctx.author.guild
        i = 0
        if len(name) > 0 and name[-1] == "exact":
            exact = True
            name = name[:-1]
        else:
            exact = False
        name = ' '.join(name)
        for member in g.members:
            for r in member.roles:
                if r.name == name or (exact == False and r.name.lower().find(name.lower()) != -1):
                    i += 1
        return i, exact, g

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['inrole', 'rolestat'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def roleStats(self, ctx, *name : str):
        """Search how many users have a matching role
        use quotes if your match contain spaces
        add 'exact' at the end to force an exact match"""
        i, exact, g = await self.bot.do(self._roleStats, ctx, name)
        if exact != "exact":
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Roles containing: {}".format(name), description="{} user(s)".format(i), thumbnail=g.icon_url, footer="on server {}".format(g.name), color=self.color))
        else:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Roles matching: {}".format(name), description="{} user(s)".format(i), thumbnail=g.icon_url, footer="on server {}".format(g.name), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 20)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def iam(self, ctx, *, role_name : str):
        """Add a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(ctx.guild.id)
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if role_name.lower() not in roles:
            await self.bot.util.react(ctx.message, '❎') # negative check mark
        else:
            id = roles[role_name.lower()]
            r = ctx.guild.get_role(id)
            if r is None: # role doesn't exist anymore
                await self.bot.util.react(ctx.message, '❎') # negative check mark
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(role_name.lower())
                    if len(self.bot.data.save['assignablerole'][g]) == 0:
                        self.bot.data.save['assignablerole'].pop(g)
                    self.bot.data.pending = True
            else:
                try:
                    await ctx.author.add_roles(r)
                except:
                    pass
                await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['iamn'])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def iamnot(self, ctx, *, role_name : str):
        """Remove a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(ctx.guild.id)
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if role_name.lower() not in roles:
            await self.bot.util.react(ctx.message, '❎') # negative check mark
        else:
            id = roles[role_name.lower()]
            r = ctx.guild.get_role(id)
            if r is None: # role doesn't exist anymore
                await self.bot.util.react(ctx.message, '❎') # negative check mark
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(role_name.lower())
                    if len(self.bot.data.save['assignablerole'][g]) == 0:
                        self.bot.data.save['assignablerole'].pop(g)
                    self.bot.data.pending = True
            else:
                try:
                    await ctx.author.remove_roles(r)
                except:
                    pass
                await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def lsar(self, ctx, page : int = 1):
        """List the self-assignable roles available in this server"""
        g = str(ctx.guild.id)
        if page < 1: page = 1
        roles = self.bot.data.save['assignablerole'].get(g, {})
        if len(roles) == 0:
            await ctx.reply(embed=self.bot.util.embed(title="Error", description="No self assignable roles available on this server", color=self.color))
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
            r = ctx.guild.get_role(roles[k])
            if r is not None:
                fields[-1]['value'] += '{}\n'.format(k)
            else:
                with self.bot.data.lock:
                    self.bot.data.save['assignablerole'][g].pop(k)
                    self.bot.data.pending = True
            count += 1

        final_msg = await ctx.reply(embed=self.bot.util.embed(title="Self Assignable Roles", fields=fields, footer="Page {}/{}".format(page, 1+len(roles)//20), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 30)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def asar(self, ctx, *, role_name : str = ""):
        """Add a role to the list of self-assignable roles (Mod Only)"""
        if role_name == "":
            await self.bot.util.react(ctx.message, '❎') # negative check mark
            return
        role = None
        for r in ctx.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await self.bot.util.react(ctx.message, '❎') # negative check mark
            return
        id = str(ctx.guild.id)
        with self.bot.data.lock:
            if id not in self.bot.assignablerole:
                self.bot.assignablerole[id] = {}
            if role.name.lower() in self.bot.assignablerole[id]:
                await self.bot.util.react(ctx.message, '❎') # negative check mark
                return
            self.bot.assignablerole[id][role.name.lower()] = role.id
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def rsar(self, ctx, *, role_name : str = ""):
        """Remove a role from the list of self-assignable roles (Mod Only)"""
        if role_name == "":
            await self.bot.util.react(ctx.message, '❎') # negative check mark
            return
        role = None
        for r in ctx.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await self.bot.util.react(ctx.message, '❎') # negative check mark
            return
        id = str(ctx.guild.id)
        with self.bot.data.lock:
            if id not in self.bot.assignablerole:
                self.bot.assignablerole[id] = {}
            if role.name.lower() not in self.bot.assignablerole[id]:
                await self.bot.util.react(ctx.message, '❎') # negative check mark
                return
            self.bot.assignablerole[id].pop(role.name.lower())
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark