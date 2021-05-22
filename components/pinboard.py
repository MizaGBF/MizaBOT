import discord

# ----------------------------------------------------------------------------------------------------------------
# Pinboard Component
# ----------------------------------------------------------------------------------------------------------------
# Enable the pinboard system ("extra pinned messages") in specific server
# Only available in 2 servers and not intended for public use
# ----------------------------------------------------------------------------------------------------------------

class Pinboard():
    def __init__(self, bot):
        self.bot = bot
        self.cache = [] # store pinned messages until reboot
        self.servers = []

    def init(self):
        self.servers = [
            {'tracked' : [self.bot.data.config['ids'].get('you_general', -1)], 'emoji': '📌', 'mod_bypass':True, 'threshold':3, 'output': 'you_pinned'},
            {'tracked' : [self.bot.data.config['ids'].get('gbfg_general', -1)], 'emoji': '⭐', 'mod_bypass':False, 'threshold':5, 'output': 'gbfg_pinned'}
        ]

    async def check(self, payload):
        try:
            idx = None
            for i in range(0, len(self.servers)):
                if payload.channel_id in self.servers[i]['tracked']:
                    idx = i
                    break
            if idx is None:
                return
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if message.id in self.cache: return
            reactions = message.reactions
        except Exception as e:
            await self.bot.sendError('raw_react', str(e))
            return
        me = message.guild.me
        count = 0
        for reaction in reactions:
            if reaction.emoji == self.servers[idx]['emoji']:
                users = await reaction.users().flatten()
                count = len(users)
                guild = message.guild
                content = message.content
                isMod = False
                count = 0
                if me in users: return
                for u in users:
                    if self.servers[idx]['mod_bypass']: # mod check
                        m = guild.get_member(u.id)
                        if m.guild_permissions.manage_messages: 
                            isMod = True
                            break
                        else:
                            count += 1
                    else:
                        count += 1
                if not isMod and count < self.servers[idx]['threshold']:
                    return

                if message.id in self.cache: return # anti dupe safety
                self.cache.append(message.id)
                if len(self.cache) > 20: self.cache = self.cache[5:] # limited to 20 entries
                await message.add_reaction(self.servers[idx]['emoji'])

                try:
                    dict = {}
                    dict['color'] = 0xf20252
                    dict['title'] = str(message.author)
                    if len(content) > 0: 
                        if len(content) > 1900: dict['description'] = content[:1900] + "...\n\n"
                        else: dict['description'] = content + "\n\n"
                    else: dict['description'] = ""
                    dict['thumbnail'] = {'url':str(message.author.avatar_url)}
                    dict['fields'] = []
                    # for attachments
                    if message.attachments:
                        for file in message.attachments:
                            if file.is_spoiler():
                                dict['fields'].append({'inline': True, 'name':'Attachment', 'value':f'[{file.filename}]({file.url})'})
                            elif file.url.lower().endswith(('.png', '.jpeg', '.jpg', '.gif', '.webp')) and 'image' not in dict:
                                dict['image'] = {'url':file.url}
                            else:
                                dict['fields'].append({'inline': True, 'name':'Attachment', 'value':f'[{file.filename}]({file.url})'})
                    # search for image url if no attachment
                    if 'image' not in dict:
                        s = content.find("http")
                        for ext in ['.png', '.jpeg', '.jpg', '.gif', '.webp']:
                            e = content.find(ext, s)
                            if e != -1:
                                e += len(ext)
                                break
                        if content.find(' ', s, e) == -1 and s != -1:
                            dict['image'] = {'url':content[s:e]}
                    # check embed
                    if len(message.embeds) > 0:
                        if dict['description'] == "" and len(message.embeds[0].description) > 0: dict['description'] = message.embeds[0].description + "\n\n"
                        if 'image' not in dict and message.embeds[0].image.url != discord.Embed.Empty: dict['image'] = {'url':message.embeds[0].image.url}
                        if len(message.embeds[0].title) > 0: dict['title'] += " :white_small_square: " + message.embeds[0].title
                        elif message.embeds[0].author.name != discord.Embed.Empty: dict['title'] += " :white_small_square: " + message.embeds[0].author.name
                    # add link to description
                    dict['description'] += ":earth_asia: [**Link**](https://discordapp.com/channels/{}/{}/{})\n".format(message.guild.id, message.channel.id, message.id)
                    embed = discord.Embed.from_dict(dict)
                    embed.timestamp=message.created_at
                    await self.bot.send(self.servers[idx]['output'], embed=embed)
                except Exception as x:
                    await self.bot.sendError("pinboard check", str(x))
                return