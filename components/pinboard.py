import disnake

# ----------------------------------------------------------------------------------------------------------------
# Pinboard Component
# ----------------------------------------------------------------------------------------------------------------
# Enable the pinboard system ("extra pinned messages") in specific server
# ----------------------------------------------------------------------------------------------------------------

class Pinboard():
    def __init__(self, bot):
        self.bot = bot
        self.cache = [] # store pinned messages until reboot

    def init(self):
        pass

    """check()
    Check the payload received from on_raw_reaction_add() and if it triggers a pin
    
    Parameters
    ----------
    payload: Raw Message Payload
    
    Returns
    --------
    bool: True if success, False if failure
    """
    async def check(self, payload):
        try:
            idx = None
            for s in self.bot.data.save['pinboard']:
                if payload.channel_id in self.bot.data.save['pinboard'][s]['tracked']:
                    idx = s
                    break
            if idx is None:
                return False
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if message.id in self.cache: return False
            reactions = message.reactions
        except Exception as e:
            await self.bot.sendError('raw_react', e)
            return False
        me = message.guild.me
        count = 0
        for reaction in reactions:
            if str(reaction.emoji) == self.bot.data.save['pinboard'][idx]['emoji']:
                users = await reaction.users().flatten()
                count = len(users)
                guild = message.guild
                content = message.content
                isMod = False
                count = 0
                if me in users: return False
                for u in users:
                    if self.bot.data.save['pinboard'][idx]['mod_bypass']: # mod check
                        m = await guild.get_or_fetch_member(u.id)
                        if m.guild_permissions.manage_messages: 
                            isMod = True
                            break
                        else:
                            count += 1
                    else:
                        count += 1
                if not isMod and count < self.bot.data.save['pinboard'][idx]['threshold']:
                    return False

                if message.id in self.cache: return False # anti dupe safety
                self.cache.append(message.id)
                if len(self.cache) > 20: self.cache.pop(0) # limited to 20 entries
                await message.add_reaction(self.bot.data.save['pinboard'][idx]['emoji'])

                try:
                    embed_dict = {}
                    embed_dict['color'] = 0xf20252
                    embed_dict['title'] = str(message.author)
                    if len(content) > 0: 
                        if len(content) > 1900: embed_dict['description'] = content[:1900] + "...\n\n"
                        else: embed_dict['description'] = content + "\n\n"
                    else: embed_dict['description'] = ""
                    embed_dict['thumbnail'] = {'url':str(message.author.display_avatar)}
                    embed_dict['fields'] = []
                    # for attachments
                    if message.attachments:
                        for file in message.attachments:
                            if file.is_spoiler():
                                embed_dict['fields'].append({'inline': True, 'name':'Attachment', 'value':f'[{file.filename}]({file.url})'})
                            elif file.url.lower().endswith(('.png', '.jpeg', '.jpg', '.gif', '.webp', 'jpg:thumb', 'jpg:small', 'jpg:medium', 'jpg:large', 'jpg:orig', 'png:thumb', 'png:small', 'png:medium', 'png:large', 'png:orig')) and 'image' not in embed_dict:
                                embed_dict['image'] = {'url':file.url}
                            else:
                                embed_dict['fields'].append({'inline': True, 'name':'Attachment', 'value':f'[{file.filename}]({file.url})'})
                    # search for image url if no attachment
                    if 'image' not in embed_dict:
                        s = content.find("http://")
                        if s == -1: s = content.find("https://")
                        if s != -1:
                            for ext in ['.png', '.jpeg', '.jpg', '.gif', '.webp', 'jpg:thumb', 'jpg:small', 'jpg:medium', 'jpg:large', 'jpg:orig', 'png:thumb', 'png:small', 'png:medium', 'png:large', 'png:orig']:
                                e = content.find(ext, s)
                                if e != -1:
                                    e += len(ext)
                                    break
                            if e!= -1 and content.find(' ', s, e) == -1:
                                embed_dict['image'] = {'url':content[s:e]}
                    # check embed
                    if len(message.embeds) > 0:
                        if len(message.embeds[0].description) > 0: embed_dict['fields'] = [{'inline': True, 'name':'Content', 'value':message.embeds[0].description}] + embed_dict['fields']
                        if 'image' not in embed_dict and message.embeds[0].image.url != message.embeds[0].Empty: embed_dict['image'] = {'url':message.embeds[0].image.url}
                        if len(message.embeds[0].title) > 0: embed_dict['title'] += " :white_small_square: " + message.embeds[0].title
                        elif message.embeds[0].author.name != disnake.Embed.Empty: embed_dict['title'] += " :white_small_square: " + message.embeds[0].author.name
                    # add link to description
                    embed_dict['description'] += ":earth_asia: [**Link**](https://discordapp.com/channels/{}/{}/{})\n".format(message.guild.id, message.channel.id, message.id)
                    if 'image' in embed_dict and embed_dict['image'] == disnake.Embed.Empty:
                        embed_dict.pop('image')
                    embed = disnake.Embed.from_dict(embed_dict)
                    embed.timestamp=message.created_at
                    ch = self.bot.get_channel(self.bot.data.save['pinboard'][idx]['output'])
                    await ch.send(embed=embed)
                except Exception as x:
                    await self.bot.sendError("pinboard check", "Guild `{}` : `{}`\nException:\n{}".format(message.guild, message.guild.id, self.bot.util.pexc(x)))
                return True
        return False

    """add()
    Enable the system for a guild (or overwrite its previous settings)
    
    Parameters
    ----------
    server_id: Guild ID, in string format
    tracked: List of channel IDs
    emoji: Emoji used, in string format
    mod: Boolean
    threshold: number of reactions needed to trigger a pin
    output: Pinboard channel ID
    """
    def add(self, server_id, tracked, emoji, mod, threshold, output): # parameters validity should be checked before the call
        with self.bot.data.lock:
            self.bot.data.save['pinboard'][server_id] = {'tracked' : tracked, 'emoji': emoji, 'mod_bypass':mod, 'threshold':threshold, 'output': output}
            self.bot.data.pending = True

    """remove()
    Disable the system for a guild
    
    Parameters
    ----------
    server_id: Guild ID, in string format
    """
    def remove(self, server_id):
        if server_id in self.bot.data.save['pinboard']:
            with self.bot.data.lock:
                self.bot.data.save['pinboard'].pop(server_id)
                self.bot.data.pending = True

    """get()
    Retrieve the settings for a guild
    
    Parameters
    ----------
    server_id: Guild ID, in string format
    
    Returns
    ----------
    dict: Stored settings, None if unavailable
    """
    def get(self, server_id):
        return self.bot.data.save['pinboard'].get(server_id, None)