
# ----------------------------------------------------------------------------------------------------------------
# Emote Component
# ----------------------------------------------------------------------------------------------------------------
# Register and retrieve custom emotes via keywords set in config.json
# For ease of use, set those emotes in the bot debug server
# ----------------------------------------------------------------------------------------------------------------

class Emote():
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    def init(self):
        pass

    """get()
    Retrieve an Emojii using its id set in config.json
    The Emoji is also cached for future uses
    
    Parameters
    ----------
    key: Emote key set in config.json
    
    Returns
    --------
    unknown: Discord Emoji if success, empty string if error, key if not found
    """
    def get(self, key): # retrieve a custom emote
        if key in self.cache:
            return self.cache[key]
        elif key in self.bot.data.config['emotes']:
            try:
                e = self.bot.get_emoji(self.bot.data.config['emotes'][key]) # ids are defined in config.json
                if e is not None:
                    self.cache[key] = e
                    return e
                return ""
            except:
                return ""
        return key