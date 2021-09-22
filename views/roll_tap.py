from . import BaseView
import discord

# ----------------------------------------------------------------------------------------------------------------
# Tap View
# ----------------------------------------------------------------------------------------------------------------
# View class used by gacha simulations
# It merely adds a "TAP" button
# ----------------------------------------------------------------------------------------------------------------

class Tap(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    owner_id: the id of the user responsible for the interaction, leave to None to ignore
    timeout: timeout in second before the interaction becomes invalid
    """
    def __init__(self, bot, owner_id : int = None, timeout : float = 60.0):
        super().__init__(bot, owner_id=owner_id, timeout=timeout, enable_timeout_cleanup=False)

    """tap()
    The tap button coroutine callback.
    Stop the view when called by the owner.
    
    Parameters
    ----------
    button: the Discord button
    button: a Discord interaction
    """
    @discord.ui.button(label='TAP', style=discord.ButtonStyle.blurple)
    async def tap(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.update_last(interaction)
        if not button.disabled and self.ownership_check(interaction):
            self.stopall()
            button.disabled = True
        else:
            await interaction.response.send_message("You can't press this button", ephemeral=True)