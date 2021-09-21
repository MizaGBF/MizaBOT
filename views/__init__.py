import discord

# ----------------------------------------------------------------------------------------------------------------
# Base View
# ----------------------------------------------------------------------------------------------------------------
# Base View class used as parent for the bot views
# ----------------------------------------------------------------------------------------------------------------

class BaseView(discord.ui.View):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    owner_id: the id of the user responsible for the interaction, leave to None to ignore
    timeout: timeout in second before the interaction becomes invalid
    enable_timeout_cleanup: if True, the original message will be cleaned up (if possible), if the time out is triggered
    """
    def __init__(self, bot, owner_id : int = None, timeout : float = 60.0, enable_timeout_cleanup : bool = True):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.owner_id = owner_id
        self.last_interaction = None
        self.enable_timeout_cleanup = enable_timeout_cleanup

    """update_last()
    Update the last interaction received
    Try to call once for each interaction
    
    Parameters
    ----------
    interaction: a Discord interaction
    """
    def update_last(self, interaction: discord.Interaction):
         self.last_interaction = interaction

    """ownership_check()
    Check if the interaction user id matches the owner_id set in the constructor
    
    Parameters
    ----------
    interaction: a Discord interaction
    
    Returns
    --------
    bool: True if it matches, False if not
    """
    def ownership_check(self, interaction: discord.Interaction):
        return (self.owner_id is None or interaction.user.id == self.owner_id)

    """on_timeout()
    Coroutine callback
    Called when the view times out
    """
    async def on_timeout(self):
        self.stop()
        if self.enable_timeout_cleanup:
            self.bot.util.cleanInter(self.last_interaction, 0)

    """on_error()
    Coroutine callback
    Called when the view triggers an error
    """
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction):
        self.bot.errn += 1
        await self.bot.send('debug', embed=self.bot.util.embed(title="⚠ Error caused by {}".format(interaction.user), description="{} Exception\n{}".format(item, self.bot.util.pexc(error)), thumbnail=interaction.user.avatar.url, footer='{}'.format(interaction.user.id), timestamp=self.bot.util.timestamp()))