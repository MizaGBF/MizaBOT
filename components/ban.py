
# ----------------------------------------------------------------------------------------------------------------
# Ban Component
# ----------------------------------------------------------------------------------------------------------------
# Manage Banned users
# ----------------------------------------------------------------------------------------------------------------

class Ban():
    def __init__(self, bot):
        self.bot = bot

    def init(self):
        pass

    # ban flags
    OWNER   = 0b00000001
    SPARK   = 0b00000010
    PROFILE = 0b00000100
    USE_BOT = 0b10000000

    """set()
    Ban an user for different bot functions. Also update existing bans
    
    Parameters
    ----------
    id: User discord id
    flag: Bit Mask
    """
    def set(self, id, flag):
        with self.bot.data.lock:
            if not self.check(id, flag):
                self.bot.data.save['ban'][str(id)] = self.bot.data.save['ban'].get(str(id), 0) ^ flag
                self.bot.data.pending = True

    """unset()
    Unban an user
    
    Parameters
    ----------
    id: User discord id
    """
    def unset(self, id, flag = None):
        with self.bot.data.lock:
            if str(id) in self.bot.data.save['ban']:
                if flag is None: self.bot.data.save['ban'].pop(str(id))
                elif self.check(id, flag): self.bot.data.save['ban'][str(id)] -= flag
                if self.bot.data.save['ban'][str(id)] == 0:
                    self.bot.data.save['ban'].pop(str(id))
                self.bot.data.pending = True

    """check()
    Return if the user is banned or not
    
    Parameters
    ----------
    id: User discord id
    flag: Bit Mask to compare
    
    Returns
    ----------
    bool: True if banned, False if not
    """
    def check(self, id, mask):
        return ((self.bot.data.save['ban'].get(str(id), 0) & mask) == mask)

    """get()
    Return the user bitmask
    
    Parameters
    ----------
    id: User discord id
    
    Returns
    ----------
    int: Bitmask
    """
    def get(self, id):
        return self.bot.data.save['ban'].get(str(id), 0)