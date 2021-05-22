
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

    def set(self, name, id_key : str): # "register" a channel to use with send()
        try:
            c = self.bot.get_channel(self.bot.data.config['ids'][id_key])
            if c is not None: self.cache[name] = c
        except:
            self.bot.errn += 1
            print("Invalid key: {}".format(id_key))

    def setID(self, name, id : int): # same but using an id instead of an id defined in config.json
        try:
            c = self.bot.get_channel(id)
            if c is not None: self.cache[name] = c
        except:
            self.bot.errn += 1
            print("Invalid ID: {}".format(id))

    def setMultiple(self, channel_list: list): # the above, all in one, format is [[channel_name, channel_id], ...]
        for c in channel_list:
            if len(c) == 2 and isinstance(c[0], str):
                if isinstance(c[1], str): self.set(c[0], c[1])
                elif isinstance(c[1], int): self.setID(c[0], c[1])
    
    def get(self, name):
        return self.cache.get(name, None)