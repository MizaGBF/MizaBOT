# ----------------------------------------------------------------------------------------------------------------
# Channel Component
# ----------------------------------------------------------------------------------------------------------------
# This component lets you register channels with a keyword to be later used by the send() function of the bot
# ----------------------------------------------------------------------------------------------------------------

class Channel():
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    def init(self):
        self.cache = {}

    """set()
    Register a channel with a name
    
    Parameters
    ----------
    name: Channel name
    id_key: Channel name in config.json
    """
    def set(self, name, id_key : str): # "register" a channel to use with send()
        try:
            c = self.bot.get_channel(self.bot.data.config['ids'][id_key])
            if c is not None: self.cache[name] = c
        except:
            self.bot.errn += 1
            print("Invalid key: {}".format(id_key))

    """setID()
    Register a channel with a name
    
    Parameters
    ----------
    name: Channel name
    id: Channel id
    """
    def setID(self, name, id : int): # same but using an id instead of an id defined in config.json
        try:
            c = self.bot.get_channel(id)
            if c is not None: self.cache[name] = c
        except:
            self.bot.errn += 1
            print("Invalid ID: {}".format(id))

    """setMultiple()
    Register multiple channels
    
    Parameters
    ----------
    channel_list: List of pair [name, id_key or id]
    """
    def setMultiple(self, channel_list: list): # the above, all in one, format is [[channel_name, channel_id], ...]
        for c in channel_list:
            if len(c) == 2 and isinstance(c[0], str):
                if isinstance(c[1], str): self.set(c[0], c[1])
                elif isinstance(c[1], int): self.setID(c[0], c[1])

    """get()
    Get a registered channel
    
    Parameters
    ----------
    name: Channel name. Can also pass directly a Channel ID if the channel isn't registered.
    
    Returns
    ----------
    discord.Channel: Discord Channel, None if error
    """
    def get(self, name):
        return self.cache.get(name, self.bot.get_channel(name))